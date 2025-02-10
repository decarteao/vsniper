
from threading import Thread
from requests import Session
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)



class MEXC:
    def __init__(self):
        self.session = Session()

        self.base_url = 'https://api.mexc.com'

        self.api_key = None
        self.api_secret = None

        self.pares = []
    def update_api(self, api_token: str, api_secret: str):
        self.api_key = api_token
        self.api_secret = api_secret
    def get_info_pair(self, _symbol: str):
        url = self.base_url + '/api/v3/exchangeInfo'
        r = self.session.get(url).json()

        for symbol in r["symbols"]:
            if symbol["status"] == "1" and 'LIMIT' in symbol["orderTypes"] and symbol["symbol"] == _symbol.strip(' -').upper():
                PRICE_FILTER = 0.01 # BTCUSDT: USDT minimo permitido
                LOT_SIZE = float(symbol["baseSizePrecision"]) # BTCUSDT: BTC minimo permitido
                NOTIONAL = 1

                baseAssetPrecision = symbol['baseAssetPrecision'] # BTC
                quoteAssetPrecision = symbol['quotePrecision'] # USDT

                if PRICE_FILTER > 0:
                    PRICE_FILTER = len(str(PRICE_FILTER).split('.')[1])
                    
                return True, (baseAssetPrecision, quoteAssetPrecision, PRICE_FILTER, LOT_SIZE, NOTIONAL)

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
        url = self.base_url + '/api/v3/exchangeInfo'
        r = self.session.get(url).json()

        pares = []

        for symbol in r["symbols"]:
            if symbol["status"] == "1" and 'LIMIT' in symbol["orderTypes"]:
                pares.append(symbol['baseAsset'] + '-' + symbol['quoteAsset'])
        
        self.pares = pares.copy()
        return {'pares': pares, 'n_pares': len(pares)}
    def cancel_all_orders(self):
        return []


# URL: https://www.mexc.com/pt-PT/mexc-api
# URL: https://mexcdevelop.github.io/apidocs/spot_v3_en/#websocket-market-streams


class MexcPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://wbs.mexc.com/ws'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = [] # apenas para teste, aqui sera dinamico

        self.isOn = False
    def get_order_book(self, par: str):
        return self.moedas_order_book.get(par.upper().replace('-',''))
    def on_open(self, ws: WebSocketApp):
        pass#print('==> WS Aberto <==')
        pares2send = { "method":"SUBSCRIPTION", "params":[f"spot@public.limit.depth.v3.api@{par.upper().replace('-','')}@5" for par in self.pares] }

        ws.send(dumps(pares2send))
        self.isOn = True
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if 'c' in message.keys() and 'public.limit.depth' in message['c']:
            symbol = message['s'].upper().replace('-','')
            try:
                bid = [float(c) for c in [message['d']['bids'][0]["p"], message['d']['bids'][0]["v"]]] # Oferta de Compra
                ask = [float(c) for c in [message['d']['asks'][0]["p"], message['d']['asks'][0]["v"]]] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            pass#print(f'[MEXC] ===> [{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        else:
            pass#print('[MEXC] ===> [message]:', message)
    def on_close(self, _: WebSocketApp, __, ___):
        pass#print('[MEXC] ===> [!close]')
        if self.isOn:
            self.start()
    def on_error(self, _: WebSocketApp, error: str):
        pass#print('[MEXC] ===> [!error]:', error)
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
    


