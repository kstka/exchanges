import datetime as dt
from exchanges.exchange import Exchange
from exchanges.exceptions import *


class Binance(Exchange):
    """
    https://binance-docs.github.io/apidocs/spot/en/
    https://binance-docs.github.io/apidocs/futures/en/
    """

    _FUTURES_API_URL = "https://fapi.binance.com"
    _SPOT_API_URL = "https://api.binance.com"

    _spot_quote_assets = ['BTC', 'PLN', 'NGN', 'RON', 'TUSD', 'USDT', 'PAX', 'JPY', 'FDUSD', 'UST', 'USDS', 'ZAR', 'USDC', 'RUB', 'BUSD', 'BNB', 'TRY', 'BKRW', 'DOGE', 'AEUR', 'DAI', 'ARS', 'GBP', 'ETH', 'BVND', 'IDRT', 'EUR', 'TRX', 'DOT', 'VAI', 'USDP', 'BIDR', 'UAH', 'AUD', 'XRP', 'BRL']
    _futures_quote_assets = ['BTC', 'PLN', 'NGN', 'RON', 'TUSD', 'USDT', 'PAX', 'JPY', 'FDUSD', 'UST', 'USDS', 'ZAR', 'USDC', 'RUB', 'BUSD', 'BNB', 'TRY', 'BKRW', 'DOGE', 'AEUR', 'DAI', 'ARS', 'GBP', 'ETH', 'BVND', 'IDRT', 'EUR', 'TRX', 'DOT', 'VAI', 'USDP', 'BIDR', 'UAH', 'AUD', 'XRP', 'BRL']

    _EXCHANGE_SYMBOL_SEPARATOR = ''

    def _initialize(self):
        if self._FUTURES:
            self._API_URL = self._FUTURES_API_URL
        else:
            self._API_URL = self._SPOT_API_URL

        if self._API_KEY:
            self.update_headers({'X-MBX-APIKEY': self._API_KEY})

    def _handle_request_kwargs(self, kwargs, method, timestamp, endpoint, signed):
        if signed:
            kwargs['params'].update({'timestamp': timestamp})
            signature = self._generate_signature(method, timestamp, endpoint, kwargs['params'])
            kwargs['params'].update({'signature': signature})

        return kwargs

    def _convert_symbol_to_global(self, symbol):
        """
        In case of Bianance symbol does not contain separator.
        So it is required to guess base and quote assets.
        For this case Binance quote assets will be kept in a variable inside this class
        """
        symbol_in_global_format = ''
        if self._FUTURES:
            for quote_asset in self._FUTURES_QUOTE_ASSETS:
                if symbol.endswith(quote_asset):
                    base_asset = symbol.replace(quote_asset, '')
                    symbol_in_global_format = base_asset + self._GLOBAL_SYMBOL_SEPARATOR + quote_asset
        else:
            for quote_asset in self._SPOT_QUOTE_ASSETS:
                if symbol.endswith(quote_asset):
                    base_asset = symbol.replace(quote_asset, '')
                    symbol_in_global_format = base_asset + self._GLOBAL_SYMBOL_SEPARATOR + quote_asset
        return symbol_in_global_format

    def get_exchange_info(self):
        if self._FUTURES:
            endpoint = '/fapi/v1/exchangeInfo'
        else:
            endpoint = '/api/v3/exchangeInfo'

        response = self._request(endpoint=endpoint)

        # parse symbols info
        for info in response['symbols']:
            symbol_info = {}

            # это костыль. У Бинанс появились странные символы вроде 'BTCUSDT_240329'
            if self._FUTURES and '_' in info['symbol']:
                continue

            # symbol and original symbol
            symbol_info['symbol'] = info['baseAsset'] + self._GLOBAL_SYMBOL_SEPARATOR + info['quoteAsset']
            symbol_info['original_symbol'] = info['symbol']

            # assets
            symbol_info['base_asset'] = info['baseAsset']
            symbol_info['quote_asset'] = info['quoteAsset']

            # status
            symbol_info['status'] = info['status']

            # filters
            symbol_info['price_precision'] = None
            symbol_info['lot_precision'] = None
            symbol_info['min_notional'] = None
            for f in info['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    symbol_info['price_precision'] = self.get_precision(f['tickSize'])
                elif f['filterType'] == 'LOT_SIZE':
                    symbol_info['lot_precision'] = self.get_precision(f['stepSize'])
                elif f['filterType'] == 'MIN_NOTIONAL' and self._FUTURES:
                    symbol_info['min_notional'] = float(f['notional'])
                elif f['filterType'] == 'NOTIONAL':
                    symbol_info['min_notional'] = float(f['minNotional'])

            if symbol_info['symbol'] is None:
                print(symbol_info)
            self.symbols_info[symbol_info['symbol']] = symbol_info

        # update quote assets
        # so far usefull for Binance only because it's symbols do not contain separator
        quote_assets = set()
        for info in response['symbols']:
            quote_assets.add(info['quoteAsset'])
        if self._FUTURES:
            self._FUTURES_QUOTE_ASSETS = list(quote_assets)
        else:
            self._SPOT_QUOTE_ASSETS = list(quote_assets)

        return self.symbols_info

    def get_balances(self):
        if self._FUTURES:
            endpoint = '/fapi/v2/account'
        else:
            endpoint = '/api/v3/account'

        response = self._get(endpoint, signed=True)

        if self._FUTURES:
            for item in response['assets']:
                self.balances[item['asset']] = {
                    'total': float(item['walletBalance']) + float(item['unrealizedProfit']),
                    'free': float(item['walletBalance']),
                    'locked': float(item['unrealizedProfit'])
                }
        else:
            for item in response['balances']:
                self.balances[item['asset']] = {
                    'total': float(item['free']) + float(item['locked']),
                    'free': float(item['free']),
                    'locked': float(item['locked'])
                    }

        return self.balances

    def get_tickers(self):
        if self._FUTURES:
            endpoint = '/fapi/v2/ticker/price'
        else:
            endpoint = '/api/v3/ticker/price'

        # [{'symbol': 'ZRXUSDT', 'price': '1.2234', 'time': 1710931501565},
        # {'symbol': 'REEFUSDT', 'price': '0.002789', 'time': 1710931501281},]
        response = self._request(endpoint=endpoint)
        result = {}
        for item in response:
            symbol = self._convert_symbol_to_global(item['symbol'])
            result[symbol] = {
                'price': float(item['price']),
                'price_str': item['price'],
            }

        return result

    def get_ticker(self, symbol):
        if self._FUTURES:
            endpoint = '/fapi/v2/ticker/price'
        else:
            endpoint = '/api/v3/ticker/price'

        symbol = self._convert_symbol_to_local(symbol)
        params = {
            'symbol': symbol,
            }
        # {'symbol': 'YGGUSDT', 'price': '0.7399000', 'time': 1710931387892}
        response = self._request(endpoint=endpoint, params=params)

        return float(response['price']), response['price']

    def create_order(self, symbol, side, quantity, price=None, stop_price=None, type='LIMIT', time_in_force=None):
        symbol = self._convert_symbol_to_local(symbol)
        side = side.upper()
        type = type.upper()

        if self._FUTURES:
            endpoint = '/fapi/v1/order'
        else:
            endpoint = '/api/v3/order'

        if type == 'LIMIT':
            if not time_in_force:
                time_in_force = self.TIME_IN_FORCE_GTC
            params = {
                'symbol': symbol,
                'side': side,
                'type': type,
                'quantity': quantity,
                'timeInForce': time_in_force,
                'price': price,
            }

        elif type == 'MARKET':
            params = {
                'symbol': symbol,
                'side': side,
                'type': type,
                'quantity': quantity,
            }
        elif type in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']:
            params = {
                'symbol': symbol,
                'side': side,
                'type': type,
                'quantity': quantity,
                'stopPrice': stop_price,
            }
        else:
            raise ExchangeException('Unknown order type: %s' % type)

        response = self._request(endpoint=endpoint, params=params, method='post', signed=True)
        return self._parse_order(response)

    def _parse_order(self, order):
        symbol = self._convert_symbol_to_global(order['symbol'])
        base_asset, quote_asset = self.get_symbol_assets(symbol)
        result = {
            'symbol': symbol,
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'order_id': str(order['orderId']),
            'price': float(order['price']), 'price_str': order['price'],
            'quantity': float(order['executedQty']), 'quantity_str': order['executedQty'],
            'orig_qty': float(order['origQty']), 'orig_qty_str': order['origQty'],
            'status': order['status'].lower(),
            'type': order['type'].lower(),
            'side': order['side'].lower(),
            'timestamp': int(dt.datetime.utcnow().timestamp()),
            }
        if 'time' in order:
            result['timestamp'] = order['time'] // 1000
        if 'cummulativeQuoteQty' in order:  # в фьючерсах есть cumQuote, может это оно
            result['quote_qty'] = float(order['cummulativeQuoteQty'])
            result['quote_qty_str'] = order['cummulativeQuoteQty']
        else:
            result['quote_qty'] = round(result['price'] * result['quantity'], 8)
            result['quote_qty_str'] = '{:0.0{}f}'.format(result['quote_qty'], 8)
        # partially_filled status
        if result['quantity'] and result['status'] == 'canceled':
            result['status'] = 'partially_filled'
        # stop price
        if 'stopPrice' in order:
            result['stop_price'] = float(order['stopPrice'])
            result['stop_price_str'] = order['stopPrice']
        else:
            result['stop_price'] = 0
            result['stop_price_str'] = ''
        return result

    def get_position_info(self, symbol):
        if self._FUTURES:
            endpoint = '/fapi/v2/positionRisk'
        else:
            raise ExchangeException('get_position_info is not supported for spot exchange')

        params = {
            'symbol': self._convert_symbol_to_local(symbol),
        }

        response = self._request(endpoint=endpoint, signed=True, params=params)
        return self._parse_position_info(response[0])

    def get_positions_info(self):
        if self._FUTURES:
            endpoint = '/fapi/v2/positionRisk'
        else:
            raise ExchangeException('get_positions_info is not supported for spot exchange')

        response = self._request(endpoint=endpoint, signed=True)
        result = {}
        for item in response:
            result[self._convert_symbol_to_global(item['symbol'])] = self._parse_position_info(item)
        return result

    @staticmethod
    def _parse_position_info(self, position_info):
        """
        {
            'symbol': 'YGGUSDT',
            'positionAmt': '0',
            'entryPrice': '0.0',
            'breakEvenPrice': '0.0',
            'markPrice': '0.73743796',
            'unRealizedProfit': '0.00000000',
            'liquidationPrice': '0',
            'leverage': '20',
            'maxNotionalValue': '25000',
            'marginType': 'cross',
            'isolatedMargin': '0.00000000',
            'isAutoAddMargin': 'false',
            'positionSide': 'BOTH',
            'notional': '0',
            'isolatedWallet': '0',
            'updateTime': 1710945588354,
            'isolated': False,
            'adlQuantile': 0
        }
        """
        return {
                'amount': float(position_info['positionAmt']),
                'entry_price': float(position_info['entryPrice']),
                'mark_price': float(position_info['markPrice']),
                'unrealized_profit': float(position_info['unRealizedProfit']),
                'liquidation_price': float(position_info['liquidationPrice']),
                'leverage': float(position_info['leverage']),
                'margin_type': position_info['marginType'],
                'isolated_margin': float(position_info['isolatedMargin']),
                'is_auto_add_margin': position_info['isAutoAddMargin'],
                'position_side': position_info['positionSide'],
                'notional': float(position_info['notional']),
                'isolated_wallet': float(position_info['isolatedWallet']),
                }

    def change_margin_type(self, symbol, margin_type):
        if self._FUTURES:
            endpoint = '/fapi/v1/marginType'
        else:
            raise ExchangeException('change_margin_type is not supported for spot exchange')

        params = {
            'symbol': self._convert_symbol_to_local(symbol),
            'marginType': margin_type.upper(),
        }


        response = self._request(endpoint=endpoint, signed=True, method='post', params=params)
        return response

    def change_leverage(self, symbol, leverage):
        if self._FUTURES:
            endpoint = '/fapi/v1/leverage'
        else:
            raise ExchangeException('change_leverage is not supported for spot exchange')

        params = {
            'symbol': self._convert_symbol_to_local(symbol),
            'leverage': leverage,
        }

        response = self._request(endpoint=endpoint, signed=True, method='post', params=params)
        return response

    def cancel_order(self, symbol=None, order_id=None):
        if not symbol:
            raise ExchangeException('symbol must be specified to cancel order')

        if self._FUTURES:
            endpoint = '/fapi/v1/order'
        else:
            endpoint = '/api/v3/order'

        params = {
            'symbol': self._convert_symbol_to_local(symbol),
        }

        if order_id:
            params['orderId'] = order_id

        response = self._request(endpoint=endpoint, signed=True, method='delete', params=params)
        return self._parse_order(response)

    def get_order(self, order_id=None, symbol=None):
        if not symbol or not order_id:
            raise ExchangeException('symbol and order_id must be specified to get order')

        if self._FUTURES:
            endpoint = '/fapi/v1/order'
        else:
            endpoint = '/api/v3/order'

        params = {
            'symbol': self._convert_symbol_to_local(symbol),
            'orderId': order_id
        }

        response = self._request(endpoint=endpoint, signed=True, params=params)
        return self._parse_order(response)
