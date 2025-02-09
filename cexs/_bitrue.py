
import gzip
import io
from websocket import WebSocketApp
from json import dumps, loads

from websocket import enableTrace

# enableTrace(True)


# URL: https://www.bitrue.com/api_docs_includes_file/spot/index.html#release-note-2023-03-16
# URL: https://www.bitrue.com/api_docs_includes_file/spot/index.html#market-streams-websocket


class BitruePricesMonitor:
    def __init__(self):
        self.base_url = 'wss://ws.bitrue.com/market/ws'
        self.moedas_order_book = {} # ADA/USDT => [menor preco de compra, maior preco de venda]
        self.pares = ['solusdt', 'adausdt', 'xrpusdt'] # apenas para teste, aqui sera dinamico
    def on_open(self, ws: WebSocketApp):
        print('==> WS Aberto <==')
        pares2send = {"event":"sub","params":{"cb_id":"btcusdt","channel":"market_btcusdt_simple_depth_step0"}}
        
        for par in self.pares:
            pares2send['params']['cb_id'] = par.lower()
            pares2send['params']['channel'] = f'market_{par.lower()}_simple_depth_step0'
            ws.send(dumps(pares2send))
    def on_message(self, ws: WebSocketApp, message: str):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')

        message = loads(utf8_data)
        if 'ping' in message.keys():
            ws.send(dumps({'pong': message['ping']}))
        elif 'simple_depth' in message['channel']:
            symbol = message['channel'].split('_')[1].upper()
            try:
                bid = [float(c) for c in message['tick']['buys'][0]] # Oferta de Compra
                ask = [float(c) for c in message['tick']['asks'][0]] # Oferta de Venda
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
    

b = BitruePricesMonitor()
b.start()


