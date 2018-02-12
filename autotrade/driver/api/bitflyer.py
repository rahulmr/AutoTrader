from datetime import datetime
import pybitflyer
import os
import hashlib

class BitflyerFxApiDriver():

    def get_history(self):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        result = []
        for execution in api.getchildorders(product_code="FX_BTC_JPY", child_order_state="COMPLETED"):
            result.append({'size': execution.get('size'), 'side': execution.get('side'), 'price': execution.get('price'), 'executed_at': execution.get('child_order_date')})
        return result

    def get_balance(self):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        result = {}
        positions = api.getpositions(product_code="FX_BTC_JPY")
        collateral = api.getcollateral()
        if len(positions) > 0:
            size = 0.0
            for pos in positions:
                if pos["side"] == "BUY":
                    size += float(pos['size'])
                else:
                    size += float(pos['size']) * -1
            result["BTC"] = size
            result["JPY"] = collateral['collateral']
        else:
            result["BTC"] = 0.0
            result["JPY"] = collateral['collateral']
        return result

    def execute(self, strategy_result):
        return getattr(self, strategy_result.get('action'))(strategy_result.get('amount'))

    def buy(self, amount):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        r = api.sendchildorder(product_code="FX_BTC_JPY",
                       child_order_type="MARKET",
                       side="BUY",
                       size=amount,
                       minute_to_expire=10000,
                       time_in_force="GTC"
                       )
        return r

    def sell(self, amount):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        r = api.sendchildorder(product_code="FX_BTC_JPY",
                       child_order_type="MARKET",
                       side="SELL",
                       size=amount,
                       minute_to_expire=10000,
                       time_in_force="GTC"
                       )
        return r

    def nothing(self, amount):
        print("nothing")
        return 200

    def price(self):
        api = pybitflyer.API()
        ticker =  api.ticker(product_code="FX_BTC_JPY")
        return ticker.get('best_bid')
    """
    通知用メソッド
    params: なし
    return: data
    """
    def collect_data(self):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        board = api.board(product_code="FX_BTC_JPY")
        positions = api.getpositions(product_code="FX_BTC_JPY")
        if len(positions) > 0:
            trade_id = hashlib.sha256(''.join([p['open_date'] for p in positions]).encode('utf-8')).hexdigest()[0:20]
            position = positions.pop()
            if position.get("side") == "BUY":
                profit = (float(board.get("mid_price")) - float(position.get("price"))) * float(position.get("size"))
            else:
                profit = (float(position.get("price")) - float(board.get("mid_price"))) * float(position.get("size"))
        else:
            position = None
            profit = None
            trade_id = hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest()[0:20]
        return trade_id, board.get("mid_price"), positions, profit


    def jpy_to_size(self, currency, price):
        api = pybitflyer.API()
        ticker =  api.ticker(product_code="%s_JPY" % currency)
        return float(price) / float(ticker['best_bid'])

class BitflyerApiDriver():

    def get_balance(self):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        result = {}
        for balance in api.getbalance():
            result[balance.get("currency_code")] = balance.get("available")
        return result

    def execute(self, strategy_result):
        return getattr(self, strategy_result.get('action'))(strategy_result.get('amount'))

    def buy(self, amount):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        r = api.sendchildorder(product_code="FX_BTC_JPY",
                       child_order_type="MARKET",
                       side="BUY",
                       size=self.jpy_to_size("FX_BTC", amount),
                       minute_to_expire=10000,
                       time_in_force="GTC"
                       )
        return r.status_code

    def sell(self, amount):
        api = pybitflyer.API(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
        r = api.sendchildorder(product_code="FX_BTC_JPY",
                       child_order_type="MARKET",
                       side="SELL",
                       size=amount,
                       minute_to_expire=10000,
                       time_in_force="GTC"
                       )
        return r.status_code

    def nothing(self):
        print("nothing")
        return 200

    def jpy_to_size(self, currency, price):
        api = pybitflyer.API()
        ticker =  api.ticker(product_code="%s_JPY" % currency)
        return price / ticker['best_bid']
