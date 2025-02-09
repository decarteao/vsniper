
from requests import Session
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace
from uuid import uuid4

import gzip
import io

# enableTrace(True)


# URL: https://pypi.org/project/bingX-connector/


class BingX:
    def __init__(self):
        self.session = Session()
        self.base_url = 'https://api.binance.com'

    def get_info_pair(self, symbol: str):
        return False, None
    def get_fees_pair(self, symbol: str):
        return False, None
    def get_balance(self, symbol: str):
        return False, None
    def buy(self, symbol: str, qnty: float, price: float):
        return False, None
    def sell(self, symbol: str, qnty: float, price: float):
        return False, None
    def list_all_pairs(self):
        return []
    def cancel_all_orders(self):
        return []


# URL: https://bingx-api.github.io/docs/#/en-us/spot/introduce
# URL: https://bingx-api.github.io/docs/#/en-us/spot/socket/market.html#Subscription%20transaction%20by%20transaction


class BingXPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://open-api-ws.bingx.com/market'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = ['sol-usdt', 'ada-usdt', 'xrp-usdt'] # apenas para teste, aqui sera dinamico
    def on_open(self, ws: WebSocketApp):
        print('==> WS Aberto <==')
        pares2send = {"id":"975f7385-7f28-4ef1-93af-df01cb9ebb53","reqType": "sub","dataType":"BTC-USDT@depth5"}
        #pares2send = { "method":"SUBSCRIPTION", "params":[f"spot@public.limit.depth.v3.api@{par.upper()}@5" for par in self.pares] }

        for par in self.pares:
            pares2send['id'] = str(uuid4())
            pares2send['dataType'] = f"{par.upper()}@depth5"
            ws.send(dumps(pares2send))
    def on_message(self, ws: WebSocketApp, message: str):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')

        message = loads(utf8_data)
        if "ping" in message.keys():
            print(dumps({"pong": message['ping'], "time": message['time']}))
            ws.send(dumps({"pong": message['ping'], "time": message['time']}))
        elif "dataType" in message.keys() and "depth" in message['dataType'] and message["success"]:
            symbol = message['dataType'].split('@',1)[0]
            try:
                bid = [float(c) for c in message["data"]["bids"][0]] # Oferta de Compra
                ask = [float(c) for c in message["data"]["asks"][0]] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            print(f'[{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        else:
            print('[message]:', message)
    def on_close(self, _: WebSocketApp, __, ___):
        print('[!close]')
    def on_error(self, _: WebSocketApp, error: str):
        print('[!error]:', error)
    def start(self):
        ws = WebSocketApp(self.base_url, on_open=self.on_open, on_close=self.on_close, on_error=self.on_error, on_message=self.on_message)
        ws.run_forever()


