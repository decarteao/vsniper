
from threading import Thread
from requests import Session
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)



class OKX:
    def __init__(self):
        self.session = Session()

        self.base_url = 'https://www.okx.com'

        self.api_key = None
        self.api_secret = None

        self.pares = []
    def update_api(self, api_token: str, api_secret: str):
        self.api_key = api_token
        self.api_secret = api_secret
    def get_info_pair(self, _symbol: str):
        # fazer mais tarde
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
        url = self.base_url + '/api/v5/public/instruments?instType=SPOT'
        r = self.session.get(url).json()

        pares = []

        for symbol in r["data"]:
            if symbol["state"] == "live":
                pares.append(symbol['instId'])
        
        self.pares = pares.copy()
        return {'pares': pares, 'n_pares': len(pares)}
    def cancel_all_orders(self):
        return []


# URL: https://www.okx.com/docs-v5/en/#overview
# URL: https://www.okx.com/docs-v5/en/#overview-websocket


class OKXPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://ws.okx.com:8443/ws/v5/public'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = [] # apenas para teste, aqui sera dinamico
        self.isOn = False
    def get_order_book(self, par: str):
        return self.moedas_order_book.get(par.upper())
    def on_open(self, ws: WebSocketApp):
        pass#print('==> WS Aberto <==')
        pares2send = {
            "op": "subscribe",
            "args": [
                {
                "channel": "books5",
                "instId": par.upper()
                } for par in self.pares
            ]
        }
        ws.send(dumps(pares2send))
        self.isOn = True
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if message['arg']['channel'] == 'books5':
            symbol = message['arg']['instId']
            try:
                bid = [float(c) for c in message['data'][0]['bids'][0]][:2] # Oferta de Compra
                ask = [float(c) for c in message['data'][0]['asks'][0]][:2] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            #print(f'[OKX] ===> [{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        else:
            pass#print('[OKX] ===> [message]:', message)
    def on_close(self, _: WebSocketApp, __, ___):
        pass#print('[!close]')
        if self.isOn:
            self.start()
    def on_error(self, _: WebSocketApp, error: str):
        pass#print('[!error]:', error)
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
    

