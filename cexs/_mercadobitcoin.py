
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)


# URL: https://api.mercadobitcoin.net/api/v4/docs
# URL: https://ws.mercadobitcoin.net/docs/v0/#/api/PublicMessages?id=orderbook


class MBPricesMonitor:
    def __init__(self):
        self.base_url = 'wss://ws.mercadobitcoin.net/ws'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = ['solusdt', 'adausdt', 'xrpusdt', 'btcusdt', 'brlbtc'] # apenas para teste, aqui sera dinamico
    def on_open(self, ws: WebSocketApp):
        print('==> WS Aberto <==')
        pares2send = {"type":"subscribe", "subscription": {"id": "BRLBTC", "name":"orderbook", "limit":10}}
        
        for par in self.pares:
            pares2send['subscription']['id'] = par.upper()
            ws.send(dumps(pares2send))
    def on_message(self, ws: WebSocketApp, message: str):
        message = loads(message)
        if 'type' in message.keys() and 'orderbook' == message['type']:
            symbol = message['id']
            try:
                bid = [float(c) for c in message['data']['bids'][0]][::-1] # Oferta de Compra
                ask = [float(c) for c in message['data']['asks'][0]][::-1] # Oferta de Venda
            except:
                bid = [0,0]
                ask = [0,0]

            print(f'[{symbol}] :: ASK => {ask} | BID: {bid} | QUER COMPRAR > QUER VENDER: {bid[0] > ask[0]}')
            self.moedas_order_book[symbol] = [bid, ask]
        elif 'type' in message.keys() and 'ping' == message['type']:
            ws.send(dumps({'type':'pong'}))
        else:
            print('[message]:', message)
    def on_close(self, _: WebSocketApp, __, ___):
        print('[!close]')
    def on_error(self, _: WebSocketApp, error: str):
        print('[!error]:', error)
    def start(self):
        ws = WebSocketApp(self.base_url, on_open=self.on_open, on_close=self.on_close, on_error=self.on_error, on_message=self.on_message)
        ws.run_forever()
    

b = MBPricesMonitor()
b.start()


