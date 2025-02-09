
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)


# URL: https://www.mexc.com/pt-PT/mexc-api
# URL: https://mexcdevelop.github.io/apidocs/spot_v3_en/#websocket-market-streams


class MexcPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://wbs.mexc.com/ws'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = ['solusdt', 'adausdt', 'xrpusdt'] # apenas para teste, aqui sera dinamico
    def on_open(self, ws: WebSocketApp):
        print('==> WS Aberto <==')
        pares2send = { "method":"SUBSCRIPTION", "params":[f"spot@public.limit.depth.v3.api@{par.upper()}@5" for par in self.pares] }

        ws.send(dumps(pares2send))
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if 'public.limit.depth' in message['c']:
            symbol = message['s']
            try:
                bid = [float(c) for c in [message['d']['bids'][0]["p"], message['d']['bids'][0]["v"]]] # Oferta de Compra
                ask = [float(c) for c in [message['d']['asks'][0]["p"], message['d']['asks'][0]["v"]]] # Oferta de Venda
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
    

b = MexcPricesMonitor()
b.start()


