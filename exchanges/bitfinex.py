import json
import hmac
import hashlib
import datetime as dt
from exchanges.exchange import Exchange
from exchanges.exceptions import *


class Bitfinex(Exchange):
    """
    https://docs.bitfinex.com/docs/introduction
    """

    _PUBLIC_API_URL = "https://api-pub.bitfinex.com"
    _SIGNED_API_URL = "https://api.bitfinex.com"

    INTERVALS = {'1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h', '3h': '3h',
                 '6h': '6h', '12h': '12h', '1d': '1D', '1w': '1W', '14d': '14D', '1m': '1M'}

    _currenсies = ["1INCH", "AAVE", "AAVEF0", "ADA", "ADAF0", "AIOZ", "ALG", "ALGF0", "ALT2612", "AMP", "APE", "APEF0", "APENFT",
                   "APP","APT","APTF0","ARB","ARBETH","ARBF0","ATH","ATO","ATOF0","AUSDT","AUSTRALIA200IXF0","AVAX",
                   "AVAXC","AVAXF0","AXS","AXSF0","AZERO","B2M","BAL","BAND","BAT","BCH","BCHN","BEST","BFX","BG1",
                   "BG2","BGB","BLAST","BLASTETH","BLUR","BMN","BNBF0","BOBA","BONK","BORG","BOSON","BTC","BTCDOMF0",
                   "BTCF0","BTT","BVIVF0","BXN","CAD","CCD","CELO","CHEX","CHF","CHZ","CNH","CNHT","COMP","COMPF0",
                   "COQ","CRV","CRVF0","DAI","DOGE","DOGEF0","DORA","DOT","DOTF0","DRK","DSH","DUSK","DVF","DYM",
                   "EGLD","EGLDF0","ENA","EOS","EOSF0","ETC","ETCF0","ETH","ETH2P","ETH2R","ETH2U","ETH2X","ETHF0",
                   "ETHS","ETHW","EUR","EURF0","EUROPE50IXF0","EUT","EUTF0","EVIVF0","EXRD","FCL","FET","FIL","FILF0",
                   "FLOKI","FLR","FORTH","FRANCE40IXF0","FTM","FTMF0","FUN","GALA","GALAF0","GBP","GBPF0",
                   "GERMANY40IXF0","GMMT","GNO","GOC","GOMINING","GRT","GTX","HILSV","HIX","HKD","HMT","HMTPLG",
                   "HONGKONG50IXF0","HTX","ICP","ICPF0","IDX","INJ","IOT","IOTF0","JAPAN225IXF0","JASMY","JASMYF0",
                   "JPY", "JPYF0", "JST", "JUP", "KAN", "KARATE", "KAVA", "KNC", "KNCF0", "KSM", "LBT", "LDO", "LEO", "LES", "LET",
                   "LIFIII", "LINK", "LINKF0", "LNX", "LRC", "LTC", "LTCF0", "LUNA2", "LUNAF0", "LYM", "MATIC", "MATICF0", "MATICM",
                   "MEME", "MEW", "MIM", "MKR", "MKRF0", "MLN", "MNA", "MODE", "MODEETH", "MPC", "MXNT", "NEAR", "NEARF0", "NEO",
                   "NEOF0", "NEOGAS", "NEXO", "NOM", "NOT", "NXRA", "OGN", "OMG", "OMGF0", "OMN", "OPX", "OPXETH", "PAX", "PEPE",
                   "PLU", "PNK", "PORTAL", "QRDO", "QTF", "QTM", "REQ", "RLY", "RRT", "SAND", "SANDF0", "SEI", "SENATE", "SGB", "SGD",
                   "SHIB", "SHIBF0", "SIDUS", "SMR", "SNX", "SOL", "SOLF0", "SPAIN35IXF0", "SPEC", "SPELL", "STG", "STGF0", "STRK",
                   "SUI", "SUKU", "SUN", "SUSHI", "SUSHIF0", "SWEAT", "SWEATNEP", "TAIKO", "TAIKOETH", "TESTADA", "TESTADAF0",
                   "TESTALGO", "TESTALGOF0", "TESTAPT", "TESTAPTF0", "TESTAVAX", "TESTAVAXF0", "TESTBTC", "TESTBTCF0",
                   "TESTDOGE", "TESTDOGEF0", "TESTDOT", "TESTDOTF0", "TESTEOS", "TESTEOSF0", "TESTETH", "TESTETHF0", "TESTFIL",
                   "TESTFILF0", "TESTLTC", "TESTLTCF0", "TESTMATIC", "TESTMATICF0", "TESTNEAR", "TESTNEARF0", "TESTSOL",
                   "TESTSOLF0", "TESTUSD", "TESTUSDT", "TESTUSDTF0", "TESTXAUT", "TESTXAUTF0", "TESTXTZ", "TESTXTZF0", "THB",
                   "THETA", "TIA", "TLOS", "TOKEN", "TOMI", "TON", "TRADE", "TRX", "TRXF0", "TRY", "TRYF0", "TSD", "TWD", "UDC",
                   "UK100IXF0", "UKOILF0", "UNI", "UNIF0", "UOS", "USD", "UST", "USTF0", "VELAR", "VET", "VRA", "WAVES", "WAVESF0",
                   "WBT", "WHBT", "WIF", "WILD", "WLDF0", "WMINIMA", "WNCG", "WOO", "WXX", "XAGF0", "XAUT", "XAUTF0", "XCAD", "XDC",
                   "XLM", "XLMF0", "XMR", "XMRF0", "XPDF0", "XPTF0", "XRD", "XRP", "XRPF0", "XTP", "XTZ", "XTZF0", "XVG", "YFI",
                   "ZEC", "ZECF0", "ZETA", "ZIL", "ZKETH", "ZKX", "ZKXETH", "ZRO", "ZRX"]
    _quote_assets = set(['BTC', 'CNHT', 'ETH', 'EUR', 'EUT', 'GBP', 'JPY', 'MIM', 'MXNT', 'TESTUSD', 'TESTUSDT', 'TRY',
                         'USD', 'UST', 'XAUT'])
    _local_symbols = {}
    _global_symbols = {}

    _EXCHANGE_SYMBOL_SEPARATOR = ''

    def _get_uri(self, endpoint, method, signed):
        if signed:
            return self._SIGNED_API_URL + endpoint
        else:
            return self._PUBLIC_API_URL + endpoint

    def _add_symbol_and_assets(self, local_symbol, global_symbol, quote_asset=None):
        if local_symbol not in self._local_symbols:
            self._local_symbols[local_symbol] = global_symbol
        if global_symbol not in self._global_symbols:
            self._global_symbols[global_symbol] = local_symbol
        if quote_asset:
            self._quote_assets.add(quote_asset)

    def _convert_symbol_to_local(self, symbol):
        if symbol in self._global_symbols:
            return self._global_symbols[symbol]
        else:
            # this is not correctly right
            # exchange_info should be called before this method
            return symbol.replace(self._GLOBAL_SYMBOL_SEPARATOR, '')

    def _convert_symbol_to_global(self, symbol):
        """
        Some Bitfinex symbol does not contain separator.
        But it is possible to get list of currencies and check if symbol ends with any of them.
        """
        symbol_in_global_format = None
        # check if symbol is already in global format
        if symbol in self._local_symbols:
            symbol_in_global_format = self._local_symbols[symbol]
        # check if symbol is in format 'BTC:USD'
        elif ':' in symbol:
            assets = symbol.split(':')
            symbol_in_global_format = assets[0] + self._GLOBAL_SYMBOL_SEPARATOR + assets[1]
            # add info about symbol and quote asset
            self._add_symbol_and_assets(symbol, symbol_in_global_format, assets[1])
        # check if symbol is in format 'BTCUSD'
        else:
            # check if symbol ends with any of the quote assets
            for quote_asset in self._quote_assets:
                if symbol.endswith(quote_asset):
                    base_asset = symbol.replace(quote_asset, '')
                    symbol_in_global_format = base_asset + self._GLOBAL_SYMBOL_SEPARATOR + quote_asset
                    # add info about symbol and quote asset
                    self._add_symbol_and_assets(symbol, symbol_in_global_format)
            # finally check if symbol ends with any of the currencies
            if not symbol_in_global_format:
                for currency in self._currensies:
                    if symbol.endswith(currency):
                        base_asset = symbol.replace(currency, '')
                        symbol_in_global_format = base_asset + self._GLOBAL_SYMBOL_SEPARATOR + currency
                        # add info about symbol and quote asset
                        self._add_symbol_and_assets(symbol, symbol_in_global_format, currency)

        return symbol_in_global_format

    def get_exchange_info(self):
        # https://docs.bitfinex.com/reference/rest-public-conf
        # get all currencies
        endpoint = '/v2/conf/pub:list:currency'
        response = self._request(endpoint=endpoint)
        self._currensies = response[0]

        if self._FUTURES:
            endpoint = '/v2/conf/pub:info:pair:futures'
        else:
            endpoint = '/v2/conf/pub:info:pair'

        response = self._request(endpoint=endpoint)

        # parse symbols info
        for info in response[0]:
            symbol_info = {}

            # symbol and original symbol
            symbol_info['symbol'] = self._convert_symbol_to_global(info[0])
            symbol_info['original_symbol'] = info[0]

            # assets
            symbol_info['base_asset'] = self.get_symbol_assets(symbol_info['symbol'])[0]
            symbol_info['quote_asset'] = self.get_symbol_assets(symbol_info['symbol'])[1]

            # status
            symbol_info['status'] = ''

            # filters
            # info[1][3] - MIN_ORDER_SIZE
            # info[1][4] - MAX_ORDER_SIZE
            symbol_info['price_precision'] = None
            symbol_info['lot_precision'] = None
            symbol_info['min_notional'] = None

            self.symbols_info[symbol_info['symbol']] = symbol_info

        return self.symbols_info

    def _parse_candle(self, candle):
        timestamp = candle[0] // 1000
        date_time = dt.datetime.utcfromtimestamp(timestamp)
        return {
            'date': date_time.date(),
            'date_time': date_time,
            'timestamp': timestamp,
            'open': candle[1],
            'close': candle[2],
            'high': candle[3],
            'low': candle[4],
            'volume': candle[5],
        }

    def get_candles(self, symbol: str, interval: str, start: int=None, end: int=None, limit: int=None):
        # https://docs.bitfinex.com/reference/rest-public-candles
        local_symbol = self._convert_symbol_to_local(symbol)
        local_interval = self.interval_to_local(interval)
        candle = f'trade:{local_interval}:t{local_symbol}'
        section = 'hist'
        endpoint = f'/v2/candles/{candle}/{section}'

        params = {
            'sort': +1,
            }
        if start:
            params['start'] = str(start * 1000)
        if end:
            params['end'] = str(end * 1000)
        if limit:
            params['limit'] = limit

        response = self._request(endpoint=endpoint, params=params)
        return [self._parse_candle(item) for item in response]

    def get_tickers(self):
        # https://docs.bitfinex.com/reference/rest-public-tickers
        endpoint = "/v2/tickers"
        params = {
            'symbols': 'ALL',
            }

        # [['tBTCUSD', 60361, 4.55098889, 60362, 6.79715111, -2535, -0.04030399, 60362, 1021.32576968, 63177, 59686],
        # ['fTESTXTZ', 0.0001, 0, 0, 0, 0.0001, 30, 9999364381.501104, 0, 0, 0.0001, 291.51188548, 0.0001, 0.0001, None, None, 0],
        # ['fALG', 0.0007450328767123288, 0, 0, 0, 0.0004, 60, 706584.39111124, -0.000284, -0.4152, 0.0004, 63332.8148604, 0.000684, 0.000684, None, None, 78689.2729467],]
        # Trading pairs starts from 't', funding pairs starts from 'f'
        response = self._request(endpoint=endpoint, params=params)
        result = {}
        for item in response:
            # check if item is trading pair
            if item[0].startswith('t'):
                symbol = self._convert_symbol_to_global(item[0].strip('t'))
                result[symbol] = {
                    'price': float(item[7]),
                    'price_str': str(item[7]),
                }

        return result
