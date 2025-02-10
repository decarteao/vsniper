
from threading import Thread
from requests import Session
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)



class Bitget:
    def __init__(self):
        self.session = Session()
        self.base_url = 'https://api.bitget.com'

        self.api_key = None
        self.api_secret = None

        self.pares = []
    def update_api(self, api_token: str, api_secret: str):
        self.api_key = api_token
        self.api_secret = api_secret
    def get_info_pair(self, symbol: str):
        try:
            r = self.session.get(self.base_url + '/api/spot/v1/public/product?symbol=' + symbol.upper().strip().replace('-',"") + '_SPBL').json()["data"]
            NOTIONAL = float(r['minTradeUSDT'])
            PRICE_FILTER = float(r['quantityScale'])

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
        r = self.session.get(self.base_url + '/api/spot/v1/public/products').json()["data"]
        pares = []

        for symbol in r:
            if symbol['status'] == "online":
                pares.append(symbol["baseCoin"] + '-' + symbol["quoteCoin"])
        
        self.pares = pares.copy()
        return {'pares': pares, 'n_pares': len(pares)}
    def cancel_all_orders(self):
        return []


# URL: https://www.bitget.com/api-doc/common/intro
# URL: https://bitgetlimited.github.io/apidoc/en/spot/#welcome


class BitgetPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://ws.bitget.com/spot/v1/stream'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = [] # apenas para teste, aqui sera dinamico
        self.isOn = False
    def get_order_book(self, par: str):
        #print(self.moedas_order_book, '=>', par.upper(), '=>', self.moedas_order_book.get(par.upper()))
        return self.moedas_order_book.get(par.upper().replace('-',''))
    def on_open(self, ws: WebSocketApp):
        pass#print('==> WS Aberto <==')
        pares2send = { "op": "subscribe", "args": [{ "instType": "sp", "channel": "books5", "instId": par.upper().replace('-','') } for par in self.pares] }

        ws.send(dumps(pares2send))
        self.isOn = True
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if message['arg']['channel'] == 'books5':
            symbol = message['arg']['instId'].upper()
            #if symbol == 'BTCUSDT':
            #print(symbol, '=>', message['data'])
            try:
                bid = [float(c) for c in message['data'][0]['bids'][0]] # Oferta de Compra
                ask = [float(c) for c in message['data'][0]['asks'][0]] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            pass#print(f'[BITGET] ===> [{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        else:
            pass#print('[BITGET] ===> [message]:', message)
    def on_close(self, _: WebSocketApp, __, ___):
        pass#print('[BITGET] ===> [!close]')
        if self.isOn:
            self.start()
    def on_error(self, _: WebSocketApp, error: str):
        pass#print('[BITGET] ===> [!error]:', error)
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
    



