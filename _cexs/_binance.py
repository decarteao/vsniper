
from threading import Thread
from websocket import WebSocketApp
from string import ascii_letters
from random import randint
from json import dumps, loads

from websocket import enableTrace
from requests import Session

from binance.client import Client
from binance.enums import TIME_IN_FORCE_FOK




# URL: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-api-information
# URL-AUTH: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/endpoint-security-type#signed-trade-and-user_data-endpoint-security


class Binance:
    def __init__(self):
        self.session = Session()
        self.base_url = 'https://api.binance.com'
        self.api_key = None
        self.api_secret = None
        self.client = Client()
        self.pares = []
    def update_api(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = Client(self.api_key, self.api_secret)
    def get_info_pair(self, symbol: str):
        url = self.base_url + '/api/v3/exchangeInfo?symbol=' + symbol.strip(' -').upper()
        r = self.session.get(url).json()

        if r["symbols"][0]["status"] == "TRADING" and 'LIMIT' in r["symbols"][0]["orderTypes"]:
            PRICE_FILTER = 0.01 # BTCUSDT: USDT minimo permitido
            LOT_SIZE = 0.00001 # BTCUSDT: BTC minimo permitido
            NOTIONAL = 1

            baseAssetPrecision = r["symbols"][0]['baseAssetPrecision'] # BTC
            quoteAssetPrecision = r["symbols"][0]['quoteAssetPrecision'] # USDT

            for _filter in r["symbols"][0]['filters']:
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
        r = self.client.get_trade_fee(symbol=symbol.strip(' -').upper())
        return (r[0]['makerCommission'], r[0]['takerCommission']) # 0.001 == 0.1%
    def get_balance(self, symbol: str):
        # {'asset': 'POL', 'free': '0.05879033', 'locked': '0.00000000'}
        return self.client.get_asset_balance(asset=symbol.strip(' -').upper())
    def buy(self, symbol: str, qnty: float, price: float):
        # (baseAssetPrecision, quoteAssetPrecision, PRICE_FILTER, LOT_SIZE, NOTIONAL)
        s,info = self.get_info_pair(symbol)
        if not s:
            return False, 'Nn conseguiu buscar os dados do par!'

        _, __, PRICE_FILTER, LOT_SIZE, NOTIONAL = info

        if LOT_SIZE == 0:
            qnty = int(qnty)
        else:
            try:
                qnty_1, qnty_2 = str(qnty).split('.')
            except:
                qnty_1, qnty_2 = str(qnty), ''

            qnty = float(qnty_1 + '.' + qnty_2[:LOT_SIZE])
        
        if PRICE_FILTER == 0:
            price = str(int(price))
        else:
            price = "{:0.0{}f}".format(price, PRICE_FILTER)

        # validar os dados de entrada
        notional_calc = float(price) * qnty
        if NOTIONAL > notional_calc:
            return False, 'Valor muito pequeno, aumente a quantidade!'

        # abrir ordem
        try:
            order = self.client.order_limit_buy(symbol=symbol.strip(' -').upper(), quantity=qnty, price=price, timeInForce=TIME_IN_FORCE_FOK)
            return True, order
        except Exception as e:
            return False, str(e)
    def sell(self, symbol: str, qnty: float, price: float):
        # (baseAssetPrecision, quoteAssetPrecision, PRICE_FILTER, LOT_SIZE, NOTIONAL)
        s,info = self.get_info_pair(symbol)
        if not s:
            return False, 'Nn conseguiu buscar os dados do par!'

        _, __, PRICE_FILTER, LOT_SIZE, NOTIONAL = info

        if LOT_SIZE == 0:
            qnty = int(qnty)
        else:
            try:
                qnty_1, qnty_2 = str(qnty).split('.')
            except:
                qnty_1, qnty_2 = str(qnty), ''

            qnty = float(qnty_1 + '.' + qnty_2[:LOT_SIZE])
        
        if PRICE_FILTER == 0:
            price = str(int(price))
        else:
            price = "{:0.0{}f}".format(price, PRICE_FILTER)

        # validar os dados de entrada
        notional_calc = float(price) * qnty
        if NOTIONAL > notional_calc:
            return False, 'Valor muito pequeno, aumente a quantidade!'

        # abrir ordem
        try:
            order = self.client.order_limit_sell(symbol=symbol.strip(' -').upper(), quantity=qnty, price=price, timeInForce=TIME_IN_FORCE_FOK)
            return True, order
        except Exception as e:
            return False, str(e)
    def list_all_pairs(self):
        url = self.base_url + '/api/v3/exchangeInfo'
        r = self.session.get(url).json()

        pares = []

        for symbol in r["symbols"]:
            if symbol["status"] == "TRADING" and 'LIMIT' in symbol["orderTypes"]:
                pares.append(symbol['baseAsset'] + '-' + symbol['quoteAsset'])
        
        self.pares = pares.copy()
        return {'pares': pares, 'n_pares': len(pares)}
    def cancel_all_orders(self):
        return self.client.cancel_all_open_orders()


# URL: https://www.binance.com/en/binance-api
# URL: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams


class BinancePricesMonitor:
    def __init__(self):
        self.base_url = 'wss://stream.binance.com:9443/ws/'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = []
        self.isOn = False
    def get_order_book(self, par: str):
        # print(self.moedas_order_book, '=>', par.lower().replace('-',''), '=>', self.moedas_order_book.get(par.lower().replace('-','')))
        return self.moedas_order_book.get(par.lower().replace('-',''))
    def streamNameGenerator(self):
        name = ''
        for i in range(randint(8, 32)):
            name += ascii_letters[randint(0, len(ascii_letters)-1)]
        return name
    def on_open(self, ws: WebSocketApp):
        pass#print('==> WS Aberto <==')
        pares2send = { "method": "SUBSCRIBE", "params": [ f"{par.lower().replace('-','')}@depth@1000ms" for par in self.pares ], "id": 1 }

        ws.send(dumps(pares2send))
        self.isOn = True
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if message["e"] == "depthUpdate":
            # order book
            symbol = message['s'].lower()
            try:
                bid = [float(c) for c in message["b"][0]] # Oferta de Compra - PRECO DE QUEM ESTA VENDO
            except:
                bid = [0,0]
            try:
                ask = [float(c) for c in message["a"][0]] # Oferta de Venda - PRECO DE QUEM ESTA QUERENDO COMPRAR
            except Exception as e:
                ask = [0,0]

            #print(f'[BINANCE] ===> [{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        else:
            pass#print('[BINANCE] ===> [message]:', message)
    def on_close(self, _: WebSocketApp):
        pass#print('[BINANCE] ===> [!close]')
        if self.isOn:
            self.start()
    def on_error(self, _: WebSocketApp, error: str):
        pass#print('[BINANCE] ===> [!error]:', error)
    def start(self):
        if self.isOn: return None
        
        self.ws = WebSocketApp(self.base_url + self.streamNameGenerator(), on_open=self.on_open, on_close=self.on_close, on_error=self.on_error, on_message=self.on_message)
        #ws.run_forever()
        Thread(target=self.ws.run_forever, args=()).start()
    def stop(self):
        self.isOn = False
        try:
            self.ws.close()
        except:
            pass
        



