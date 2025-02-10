
from threading import Thread
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
        self.base_url = 'https://open-api.bingx.com'

        self.api_key = None
        self.api_secret = None
        self.pares = []
    def update_api(self, api_token: str, api_secret: str):
        self.api_key = api_token
        self.api_secret = api_secret
    def get_info_pair(self, symbol: str):
        try:
            r = self.session.get(self.base_url + '/openApi/spot/v1/common/symbols?symbol=' + symbol.upper().strip()).json()["data"]["symbols"][0]
            NOTIONAL = r['minNotional']
            PRICE_FILTER = r['stepSize']

            return True, (NOTIONAL, PRICE_FILTER)
        except:
            pass
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
        r = self.session.get(self.base_url + '/openApi/spot/v1/common/symbols').json()["data"]["symbols"]
        pares = []

        for symbol in r:
            if symbol['apiStateSell'] and symbol['apiStateBuy']:
                pares.append(symbol["symbol"])
        
        self.pares = pares.copy()
        return {'pares': pares, 'n_pares': len(pares)}
    def cancel_all_orders(self):
        return []


# URL: https://bingx-api.github.io/docs/#/en-us/spot/introduce
# URL: https://bingx-api.github.io/docs/#/en-us/spot/socket/market.html#Subscription%20transaction%20by%20transaction


class BingXPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://open-api-ws.bingx.com/market'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = [] # apenas para teste, aqui sera dinamico
        self.isOn = False
    def get_order_book(self, par: str):
        # print(self.moedas_order_book, '=>', par.upper(), '=>', self.moedas_order_book.get(par.upper()))
        return self.moedas_order_book.get(par.upper())
    def on_open(self, ws: WebSocketApp):
        pass#print('==> WS Aberto <==')
        pares2send = {"id":"975f7385-7f28-4ef1-93af-df01cb9ebb53","reqType": "sub","dataType":"BTC-USDT@depth5"}
        #pares2send = { "method":"SUBSCRIPTION", "params":[f"spot@public.limit.depth.v3.api@{par.upper()}@5" for par in self.pares] }

        for par in self.pares:
            pares2send['id'] = str(uuid4())
            pares2send['dataType'] = f"{par.upper()}@depth5"
            ws.send(dumps(pares2send))
        
        self.isOn = True
    def on_message(self, ws: WebSocketApp, message: str):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')

        message = loads(utf8_data)
        if "ping" in message.keys():
            pass#print(dumps({"pong": message['ping'], "time": message['time']}))
            ws.send(dumps({"pong": message['ping'], "time": message['time']}))
        elif "dataType" in message.keys() and "depth" in message['dataType'] and message["success"]:
            symbol = message['dataType'].split('@',1)[0].upper()
            try:
                bid = [float(c) for c in message["data"]["bids"][0]] # Oferta de Compra
                ask = [float(c) for c in message["data"]["asks"][0]] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            pass#print(f'[BingX] ===> [{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        else:
            pass#print('[BingX] ===> [message]:', message)
    def on_close(self, _: WebSocketApp, __, ___):
        pass#print('[BingX] ===> [!close]')
        if self.isOn:
            self.start()
    def on_error(self, _: WebSocketApp, error: str):
        pass#print('[BingX] ===> [!error]:', error)
    def start(self):
        if self.isOn: return None
        
        self.ws = WebSocketApp(self.base_url, on_open=self.on_open, on_close=self.on_close, on_error=self.on_error, on_message=self.on_message)
        #ws.run_forever()
        Thread(target=self.ws.run_forever, args=()).start()
    def stop(self):
        self.isOn = False
        try:
            self.ws.close()
        except:
            pass


