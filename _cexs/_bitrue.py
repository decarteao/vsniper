
import gzip
import io
from threading import Thread
from requests import Session
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)


class Bitrue:
    def __init__(self):
        self.session = Session()
        self.base_url = 'https://openapi.bitrue.com'

        self.api_key = None
        self.api_secret = None

        self.pares = []
    def update_api(self, api_token: str, api_secret: str):
        self.api_key = api_token
        self.api_secret = api_secret
    def get_info_pair(self, _symbol: str):
        url = self.base_url + '/api/v1/exchangeInfo'
        r = self.session.get(url).json()

        for symbol in r["symbols"]:
            if symbol["status"] == "TRADING" and 'LIMIT' in symbol["orderTypes"] and symbol["symbol"] == _symbol.strip(' -').upper():
                PRICE_FILTER = 0.01 # BTCUSDT: USDT minimo permitido
                LOT_SIZE = 0.00001 # BTCUSDT: BTC minimo permitido
                NOTIONAL = 1

                baseAssetPrecision = symbol['baseAssetPrecision'] # BTC
                quoteAssetPrecision = symbol['quotePrecision'] # USDT

                for _filter in symbol['filters']:
                    if _filter['filterType'] == 'PRICE_FILTER':
                        PRICE_FILTER = float(_filter['minPrice'])
                    elif _filter['filterType'] == 'LOT_SIZE':
                        LOT_SIZE = float(_filter['minQty'])
                    elif _filter['filterType'] == 'NOTIONAL':
                        NOTIONAL = float(_filter['minNotional'])
                
                if PRICE_FILTER > 0:
                    PRICE_FILTER = len(str(PRICE_FILTER).split('.')[1])

                if LOT_SIZE > 0:
                    LOT_SIZE = len(str(LOT_SIZE).split('.')[1])
                
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
        url = self.base_url + '/api/v1/exchangeInfo'
        r = self.session.get(url).json()

        pares = []

        for symbol in r["symbols"]:
            if symbol["status"] == "TRADING" and 'LIMIT' in symbol["orderTypes"]:
                pares.append((symbol['baseAsset'] + '-' + symbol['quoteAsset']).upper())
        
        self.pares = pares.copy()
        return {'pares': pares, 'n_pares': len(pares)}
    def cancel_all_orders(self):
        return []


# URL: https://www.bitrue.com/api_docs_includes_file/spot/index.html#release-note-2023-03-16
# URL: https://www.bitrue.com/api_docs_includes_file/spot/index.html#market-streams-websocket


class BitruePricesMonitor:
    def __init__(self):
        self.base_url = 'wss://ws.bitrue.com/market/ws'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = [] # apenas para teste, aqui sera dinamico
        self.isOn = False
    def get_order_book(self, par: str):
        return self.moedas_order_book.get(par.lower().replace('-',''))
    def on_open(self, ws: WebSocketApp):
        pass#print('==> WS Aberto <==')
        pares2send = {"event":"sub","params":{"cb_id":"btcusdt","channel":"market_btcusdt_simple_depth_step0"}}
        
        for par in self.pares:
            pares2send['params']['cb_id'] = par.lower()
            pares2send['params']['channel'] = f'market_{par.lower().replace('-','')}_simple_depth_step0'
            ws.send(dumps(pares2send))
            
        self.isOn = True
    def on_message(self, ws: WebSocketApp, message: str):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')

        message = loads(utf8_data)
        if 'ping' in message.keys():
            ws.send(dumps({'pong': message['ping']}))
        elif 'simple_depth' in message['channel']:
            symbol = message['channel'].split('_')[1].lower()
            try:
                bid = [float(c) for c in message['tick']['buys'][0]] # Oferta de Compra
                ask = [float(c) for c in message['tick']['asks'][0]] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            pass#print(f'[BITRUE] ===> [{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        else:
            pass#print('[BITRUE] ===> [message]:', message)
    def on_close(self, _: WebSocketApp, __, ___):
        pass#print('[BITRUE] ===> [!close]')
        if self.isOn:
            self.start()
    def on_error(self, _: WebSocketApp, error: str):
        pass#print('[BITRUE] ===> [!error]:', error)
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
    


