
from threading import Thread
from requests import Session
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)


class MercadoBitcoin:
    def __init__(self):
        self.session = Session()
        self.base_url = 'https://api.mercadobitcoin.net/api/v4'

        self.api_key = None
        self.api_secret = None

        self.pares = []
    def update_api(self, api_token: str, api_secret: str):
        self.api_key = api_token
        self.api_secret = api_secret
    def get_info_pair(self, symbol: str):
        try:
            r = self.session.get(self.base_url + '/symbols').json()
            max_line = len(r["symbol"])

            for i in range(max_line):
                _type = r["type"][i] # CRYPTO
                _listed = r["exchange-listed"][i] # True
                if _type == 'CRYPTO' and _listed and r["symbol"][i] == symbol:
                    NOTIONAL = float(r['min-volume'][i])
                    PRICE_FILTER = float(r["min-price"][i])

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
        r = self.session.get(self.base_url + '/symbols').json()
        max_line = len(r["symbol"])

        pares = []

        for i in range(max_line):
            _type = r["type"][i] # CRYPTO
            _listed = r["exchange-listed"][i] # True
            if _type == 'CRYPTO' and _listed:
                pares.append(r['symbol'][i])
        
        self.pares = pares.copy()
        return {'pares': pares, 'n_pares': len(pares)}
    def cancel_all_orders(self):
        return []




# URL: https://api.mercadobitcoin.net/api/v4/docs
# URL: https://ws.mercadobitcoin.net/docs/v0/#/api/PublicMessages?id=orderbook


class MBPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://ws.mercadobitcoin.net/ws'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = [] # apenas para teste, aqui sera dinamico
        self.isOn = False
    def get_order_book(self, par: str):
        return self.moedas_order_book.get(''.join(par.upper().split('-')[::-1]))
    def on_open(self, ws: WebSocketApp):
        pass#print('==> WS Aberto <==')
        pares2send = {"type":"subscribe", "subscription": {"id": "BRLBTC", "name":"orderbook", "limit":10}}
        
        for par in self.pares:
            pares2send['subscription']['id'] = ''.join(par.upper().split('-')[::-1])
            ws.send(dumps(pares2send))

        self.isOn = True
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if 'type' in message.keys() and 'orderbook' == message['type']:
            symbol = message['id'].upper()
            try:
                bid = [float(c) for c in message['data']['bids'][0]] # Oferta de Compra
                ask = [float(c) for c in message['data']['asks'][0]] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            #print(f'[{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        elif 'type' in message.keys() and 'ping' == message['type']:
            ws.send(dumps({'type':'pong'}))
        else:
            pass#print('[message]:', message)
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
    



