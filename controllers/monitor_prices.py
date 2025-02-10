
from json import dumps
from _cexs._binance import Binance, BinancePricesMonitor
from _cexs._bingx import BingX, BingXPricesMonitor
from _cexs._bitget import Bitget, BitgetPricesMonitor
from _cexs._bitrue import Bitrue, BitruePricesMonitor

from _cexs._mercadobitcoin import MercadoBitcoin, MBPricesMonitor
from _cexs._mexc import MEXC, MexcPricesMonitor
from _cexs._okx import OKX, OKXPricesMonitor
from concurrent.futures import ThreadPoolExecutor


class MonitorPrices:
    def __init__(self):
        self.binance = Binance()
        self.binance_ws = BinancePricesMonitor()

        self.bingx = BingX()
        self.bingx_ws = BingXPricesMonitor()

        self.bitget = Bitget()
        self.bitget_ws = BitgetPricesMonitor()

        self.bitrue = Bitrue()
        self.bitrue_ws = BitruePricesMonitor()

        self.mb = MercadoBitcoin()
        self.mb_ws = MBPricesMonitor()

        self.mexc = MEXC()
        self.mexc_ws = MexcPricesMonitor()

        self.okx = OKX()
        self.okx_ws = OKXPricesMonitor()

        self.pares = []
        self.list_all_pares()
    def format_exchange_name(self, exchange: str):
        exchange = exchange.lower()
        if exchange == 'mercado bitcoin':
            exchange = 'mb'
        return exchange
    def buscar_pares_iguais(self, exchange1: str, exchange2: str):
        exchange1 = self.format_exchange_name(exchange1)
        exchange2 = self.format_exchange_name(exchange2)

        pares_1 = getattr(self, exchange1).list_all_pairs()
        pares_2 = getattr(self, exchange2).list_all_pairs()

        pares_comuns = []

        for par1 in (pares_1['pares'] if pares_1['n_pares'] < pares_2['n_pares'] else pares_2['pares']):
            for par2 in (pares_1['pares'] if pares_1['n_pares'] > pares_2['n_pares'] else pares_2['pares']):
                # comparar
                if par1 == par2:
                    pares_comuns.append(par1)
        
        return pares_comuns
    def __list_all_pares(self, exch: str):
        self.pares.extend(getattr(self, exch).list_all_pairs()['pares'])
    def list_all_pares(self):
        print('[!] BUSCAR PARES')
        self.pares = []

        with ThreadPoolExecutor(7) as tpe:
            tpe.map(self.__list_all_pares, ['binance', 'bingx', 'bitget', 'bitrue', 'mb', 'mexc', 'okx'])

        self.pares = sorted(list(set(self.pares)))
        print('[!] PARES BUSCADOS')
    def get_exchanges_with_par(self, par: str):
        # busca todas exchanges que possuem este par
        exch_valids = []
        for exch in ['binance', 'bingx', 'bitget', 'bitrue', 'mb', 'mexc', 'okx']:
            if par in getattr(self, exch).pares:
                exch_valids.append(exch)
        return exch_valids
    def __get_oportunity(self, _id: int, exch1: str, exch2: str, par: str, spread_min: float):
        exch1 = self.format_exchange_name(exch1)
        exch2 = self.format_exchange_name(exch2)

        info_1 = getattr(self, exch1 + '_ws').get_order_book(par)
        info_2 = getattr(self, exch2 + '_ws').get_order_book(par)

        # ADA/USDT => [menor preco de compra, maior preco de venda]
        data = {'id': _id, 'exch1': '-', 'exch2': '-', 'exch1_price': [0,0], 'exch2_price': [0,0], 'best_spread': 0}
        if info_1 and info_2 and info_1[0][0] > 0 and info_2[0][0] > 0 and info_1[1][0] > 0 and info_2[1][0] > 0:
            # calcular o spread
            info_1_bid = info_1[0] # preco de compra
            info_1_ask = info_1[1] # preco de venda

            info_2_bid = info_2[0] # preco de compra
            info_2_ask = info_2[1] # preco de venda

            casa1_para_casa2 = info_1_ask[0] - info_2_bid[0]
            casa2_para_casa1 = info_2_ask[0] - info_1_bid[0]

            menor_venda = min(info_1_bid[0], info_2_bid[0])
            maior_casa = max(casa1_para_casa2, casa2_para_casa1)
            
            best_spread = (maior_casa / menor_venda) * 100
            best_spread = float("{:0.0{}f}".format(best_spread, 3))

            if best_spread >= spread_min:
                exch1 = 'COMPRA' if info_1_bid[0] < info_2_ask[0] else 'VENDA'
                exch2 = 'VENDA' if info_1_bid[0] < info_2_ask[0] else 'COMPRA'
            else:
                exch1 = 'NADA'
                exch2 = 'NADA'

            exch1_price = info_1_bid if info_1_bid[0] < info_2_ask[0] else info_2_ask
            exch2_price = info_2_ask if info_1_bid[0] < info_2_ask[0] else info_1_bid

            data = {'id': _id, 'exch1': exch1, 'exch2': exch2, 'exch1_price': exch1_price, 'exch2_price': exch2_price, 'best_spread': best_spread}

            return data
        else:
            return data
    def get_oportunity(self, params: list):
        # for MAP THREAD
        try:
            return self.__get_oportunity(*params)
        except:
            return None

