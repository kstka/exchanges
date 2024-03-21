import base64
import hashlib
import hmac
import json
from exchanges.exceptions import *
from exchanges.exchange import Exchange


class KuCoin(Exchange):
    """A class representing the KuCoin exchange.

    This class inherits from the Exchange class.

    Attributes:
        _API_URL (str): The base URL for the KuCoin API.
        _EXCHANGE_SYMBOL_SEPARATOR (str): The separator used for exchange symbols.
        INTERVALS (dict): A dictionary mapping interval strings to their corresponding KuCoin interval strings.
    """

    _API_URL = 'https://openapi-v2.kucoin.com'
    _EXCHANGE_SYMBOL_SEPARATOR = '-'

    INTERVALS = {'1m': '1min', '3m': '3min', '5m': '5min', '15m': '15min', '30m': '30min', '1h': '1hour', '2h': '2hour',
                 '4h': '4hour', '6h': '6hour', '8h': '8hour', '12h': '12hour', '1d': '1day', '1w': '1week'}

    def _generate_signature(self, method, timestamp, path, params):
        timestamp = str(timestamp)
        data_json = ''
        endpoint = path

        if method == 'get':
            if params:
                query_string = self._generate_query_string(params)
                endpoint = path + '?' + query_string
        elif params:
            data_json = self._json_dumps(params)

        signature_string = timestamp+method.upper()+endpoint+data_json

        signature = bytes(base64.b64encode(
            hmac.new(self._API_SECRET.encode('utf-8'),
                     signature_string.encode('utf-8'),
                     hashlib.sha256).digest()))
        return signature

    def _generate_passphrase(self):
        passphrase = bytes(base64.b64encode(
            hmac.new(self._API_SECRET.encode('utf-8'),
                     self._API_PASSWORD.encode('utf-8'),
                     hashlib.sha256).digest()))

        return passphrase

    def _handle_request_kwargs(self, kwargs, method, timestamp, endpoint, signed):
        if signed:
            headers = {
                # 'Accept': 'application/json',
                'KC-API-KEY-VERSION': '2',
                'Content-Type': 'application/json',
                'KC-API-TIMESTAMP': str(timestamp),
                'KC-API-SIGN': self._generate_signature(method, timestamp, endpoint, kwargs['params']).decode(),
                'KC-API-KEY': self._API_KEY,
                'KC-API-PASSPHRASE': self._generate_passphrase().decode(),
                # 'KC-API-PASSPHRASE': self._API_PASSWORD,
                }
            kwargs['headers'].update(headers)

        if method != 'get':
            kwargs['data'] = self._json_dumps(kwargs['params'])
            del kwargs['params']

        return kwargs

    @staticmethod
    def _json_dumps(data):
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    @staticmethod
    def _handle_response(raw_response):
        """Internal helper for handling API responses from the Kucoin server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """

        if not str(raw_response.status_code).startswith('2'):
            raise ExchangeAPIException(raw_response)
        try:
            response = raw_response.json()

            if 'code' in response and response['code'] != "200000":
                raise ExchangeAPIException(raw_response)

            if 'success' in response and not response['success']:
                raise ExchangeAPIException(raw_response)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'data' in response:
                response = response['data']
            return response
        except ValueError:
            raise ExchangeRequestException(f"Invalid Response: {raw_response.text}")

    def get_balances(self):
        endpoint = '/api/v1/accounts'

        response = self._get(endpoint, signed=True)

        for item in response:
            if item['type'] == 'trade':
                self.balances[item['currency']] = {
                    'total': float(item['balance']),
                    'free': float(item['available']),
                    'locked': float(item['holds'])
                    }

        return self.balances

    def get_orders(self, symbol: str, from_timestamp=None, **kwargs):

        symbol = self._convert_symbol_to_local(symbol)

        params = {
            'symbol': symbol,
            }

        if self._SPOT:
            endpoint = '/api/v1/orders'
            # params['tradeType'] = 'TRADE'
            status = kwargs.get('status', '')
            if status:
                params['status'] = status
        elif self._FUTURES:
            endpoint = ''
        else:
            raise ExchangeException('Unknown market')

        if from_timestamp:
            from_timestamp = self._parse_timestamp(from_timestamp)
            params['startAt'] = from_timestamp

        response = self._get(endpoint, signed=True, params=params)

        items = []
        if len(response['items']):
            items = response['items']

        if response['totalPage'] > 1:
            for i in range(2, response['totalPage']+1):
                params['currentPage'] = i
                response_chunk = self._get(endpoint, signed=True, params=params)
                if len(response_chunk['items']):
                    items.extend(response_chunk['items'])

        items.reverse()
        return [self._parse_order(item) for item in items]

    def get_open_orders(self, symbol: str):
        return self.get_orders(symbol, status='active')

    def _parse_order(self, order):
        symbol = self._convert_symbol_to_global(order['symbol'])
        base_asset, quote_asset = self.get_symbol_assets(symbol)
        result = {
            'symbol': symbol,
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'order_id': str(order['id']),
            'price':  float(order['price']),
            'price_str': order['price'],
            'quantity':  float(order['dealSize']),
            'quantity_str':  order['dealSize'],
            'orig_qty': float(order['size']),
            'orig_qty_str': order['size'],
            'quote_qty': float(order['dealFunds']),
            'quote_qty_str': order['dealFunds'],
            'type':  order['type'],
            'side':  order['side'],
            'timestamp': int(order['createdAt']) // 1000,
            }
        # market order
        if order['type'] == 'market' or order['type'] == 'market_stop':
            result['orig_qty'] = result['quantity']
            result['orig_qty_str'] = result['quantity_str']
            result['price'] = round(result['quote_qty'] / result['quantity'], 8)
            result['price_str'] = '{:0.0{}f}'.format(result['price'], 8)
        # status
        if order['isActive']:
            result['status'] = 'new'
        elif order['dealFunds'] == '0' and order['dealSize'] == '0' and order['cancelExist']:
            result['status'] = 'canceled'
        elif order['type'] == 'market' or order['type'] == 'market_stop':
            result['status'] = 'filled'
        elif order['size'] == order['dealSize']:
            result['status'] = 'filled'
        else:
            result['status'] = 'partially_filled'
        return result
