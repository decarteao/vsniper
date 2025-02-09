
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)


# URL: https://www.bitget.com/api-doc/common/intro
# URL: https://bitgetlimited.github.io/apidoc/en/spot/#welcome


class BitgetPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://ws.bitget.com/spot/v1/stream'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = ['solusdt', 'adausdt', 'xrpusdt'] # apenas para teste, aqui sera dinamico
    def on_open(self, ws: WebSocketApp):
        print('==> WS Aberto <==')
        pares2send = { "op": "subscribe", "args": [{ "instType": "sp", "channel": "books5", "instId": par.upper() } for par in self.pares] }

        ws.send(dumps(pares2send))
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if message['arg']['channel'] == 'books5':
            symbol = message['arg']['instId']
            try:
                bid = [float(c) for c in message['data'][0]['bids'][0]] # Oferta de Compra
                ask = [float(c) for c in message['data'][0]['asks'][0]] # Oferta de Venda
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
    

b = BitgetPricesMonitor()
b.start()


