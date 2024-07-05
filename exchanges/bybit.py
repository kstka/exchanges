import json
import hmac
import hashlib
from exchanges.exchange import Exchange
from exchanges.exceptions import *


class ByBit(Exchange):
    """
    https://bybit-exchange.github.io/docs/v5/intro
    """

    _API_URL = "https://api.bybit.com"
    _CATEGORY = 'spot'

    _RECV_WINDOW = '5000'

    def _initialize(self):
        if self._FUTURES:
            self._CATEGORY = 'linear'

        # self.update_headers({'X-BAPI-RECV-WINDOW': '5000'})

    def _handle_request_kwargs(self, kwargs, method, timestamp, endpoint, signed):
        if signed:
            headers = {
                "Content-Type": "application/json",
                "X-BAPI-API-KEY": self._API_KEY,
                "X-BAPI-SIGN": self._generate_signature(method, timestamp, endpoint, kwargs['params']),
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": str(timestamp),
                "X-BAPI-RECV-WINDOW": self._RECV_WINDOW,
                }
            kwargs['headers'].update(headers)

        if method != 'get':
            kwargs['data'] = json.dumps(kwargs['params'])
            del kwargs['params']

        return kwargs

    def _generate_signature(self, method, timestamp, path, params):
        timestamp = str(timestamp)
        if method == 'get':
            params_string = '&'.join([f'{key}={value}' for key, value in params.items()])
        else:
            params_string = json.dumps(params)
        signature_string = timestamp + self._API_KEY + self._RECV_WINDOW + params_string
        return self._generate_hmac(signature_string)

    def _generate_hmac(self, signature_string):
        m = hmac.new(
            bytes(self._API_SECRET.encode('utf-8')),
            signature_string.encode('utf-8'),
            hashlib.sha256
            )
        return m.hexdigest()

    def _generate_request_headers(self, signed, params_string, method, timestamp):
        headers = {
            'X-BAPI-API-KEY': self._API_KEY,
            'X-BAPI-RECV-WINDOW': '5000',
            }
        if signed:
            timestamp = str(timestamp)
            signature = self._generate_signature(params_string)
            headers['X-BAPI-SIGN'] = signature
            headers['X-BAPI-TIMESTAMP'] = timestamp
            return headers
        else:
            return headers

    def _session_post(self, url, params, headers):
        return self._session.post(url,
                                  data=json.dumps(params),
                                  headers=headers,
                                  proxies=self._PROXIES,
                                  timeout=self._REQUESTS_TIMEOUT)

    def get_candles(self, symbol: str, interval: str, start: int = None, end: int = None, limit=200):
        endpoint = '/v5/market/kline'
        params = {
            'category': self._CATEGORY,
            'symbol': symbol,
            'interval': interval,
            'limit': limit
            }
        if start:
            params['start'] = start
        if end:
            params['end'] = end

        return self._request(endpoint=endpoint, params=params)

    def get_server_time(self):
        endpoint = '/v5/market/time'

        return self._request(endpoint=endpoint)

    def get_tickers(self, **kwargs):
        endpoint = "/v5/market/tickers"
        params = {
            'category': self._CATEGORY,
            }
        if 'symbol' in kwargs:
            params['symbol'] = kwargs['symbol']

        return self._request(endpoint=endpoint, params=params)

    def get_balances(self):
        """Get wallet balance,
        query asset information of each currency, and account risk rate information under unified margin mode.
        By default, currency information with assets or liabilities of 0 is not returned.

        Required args:
            accountType (string): Account type
                Unified account: UNIFIED
                Normal account: CONTRACT

        Returns:
            Request results as dictionary.

        Additional information:
            https://bybit-exchange.github.io/docs/v5/account/wallet-balance
        """

        if self._FUTURES:
            account_type = 'CONTRACT'
        else:
            account_type = 'SPOT'

        endpoint = '/v5/account/wallet-balance'
        params = {
            'accountType': account_type
            }

        response = self._request(endpoint=endpoint, params=params, signed=True)

        return response

    def get_open_orders(self, symbol: str):
        # https://bybit-exchange.github.io/docs/v5/order/open-order
        endpoint = '/v5/order/realtime'
        params = {
            'category': self._CATEGORY,
            'symbol': symbol
            }

        response = self._request(endpoint=endpoint, params=params, signed=True)
        return response
