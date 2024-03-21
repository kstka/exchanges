import requests
import time
import math
import hmac
import hashlib
from exchanges.exceptions import *


class Exchange:

    symbols_info = {}  # holds all symbols info after exchange_info request
    balances = {}  # holds all balances after balances request
    tickers = {}  # holds all tickers after tickers request

    _GLOBAL_SYMBOL_SEPARATOR = '/'  # global (common) symbol separator
    _EXCHANGE_SYMBOL_SEPARATOR = '/'  # exchange symbol separator

    _API_URL = ''

    INTERVALS = {'1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                 '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d', '1w': '1w'}

    SIDE_BUY = 'BUY'
    SIDE_SELL = 'SELL'

    ORDER_TYPE_LIMIT = 'LIMIT'
    ORDER_TYPE_MARKET = 'MARKET'
    ORDER_TYPE_STOP = 'STOP'
    ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
    ORDER_TYPE_STOP_MARKET = 'STOP_MARKET'
    ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
    ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
    ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
    ORDER_TYPE_TAKE_PROFIT_MARKET = 'TAKE_PROFIT_MARKET'
    ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'

    TIME_IN_FORCE_GTC = 'GTC'  # Good till cancelled
    TIME_IN_FORCE_IOC = 'IOC'  # Immediate or cancel
    TIME_IN_FORCE_FOK = 'FOK'  # Fill or kill

    MARGIN_TYPE_CROSSED = 'CROSSED'
    MARGIN_TYPE_ISOLATED = 'ISOLATED'

    ORDER_STATUS_NEW = 'NEW'
    ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    ORDER_STATUS_FILLED = 'FILLED'
    ORDER_STATUS_CANCELED = 'CANCELED'
    ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL'
    ORDER_STATUS_REJECTED = 'REJECTED'
    ORDER_STATUS_EXPIRED = 'EXPIRED'

    def __init__(self,
                 api_key=None,
                 api_secret=None,
                 api_password=None,
                 proxies=None,
                 futures=False,
                 requests_params=None,
                 requests_timeout=10):

        self._API_KEY = api_key
        self._API_SECRET = api_secret
        self._API_PASSWORD = api_password
        self._PROXIES = proxies
        self._FUTURES = futures
        self._SPOT = False if futures else True
        self._REQUESTS_PARAMS = requests_params
        self._REQUESTS_TIMEOUT = requests_timeout
        self._session = self._init_session()
        self._init_proxies()
        self._initialize()

    def _convert_symbol_to_local(self, symbol):
        return symbol.replace(self._GLOBAL_SYMBOL_SEPARATOR, self._EXCHANGE_SYMBOL_SEPARATOR)

    def _convert_symbol_to_global(self, symbol):
        return symbol.replace(self._EXCHANGE_SYMBOL_SEPARATOR, self._GLOBAL_SYMBOL_SEPARATOR)

    def _send_symbol(self, symbol):
        pass

    @staticmethod
    def _parse_timestamp(timestamp) -> int:
        """
        :param timestamp: The timestamp to be parsed. It can be of type int, float, or str.
        :return: The parsed timestamp in milliseconds.

        This method takes a timestamp as input and returns the parsed timestamp in milliseconds.
        The timestamp can be provided as an int, float, or str. If a str is provided, it will be parsed
        into a numeric value. If the timestamp is already in seconds, it will be converted to milliseconds.

        Raises a ValueError if the string provided for timestamp is not numeric.
        Raises a TypeError if the type of timestamp is not int, float, or str.
        """
        if isinstance(timestamp, str):
            try:
                timestamp = int(float(timestamp))
            except ValueError:
                raise ValueError("Invalid string for timestamp. Must be numeric.")
        elif isinstance(timestamp, float):
            timestamp = int(timestamp)
        elif not isinstance(timestamp, int):
            raise TypeError("Timestamp must be of type int, float, or str.")

        # Check if timestamp is in seconds (smaller than 1e12)
        if timestamp < 1e12:
            # If in seconds, convert to milliseconds
            timestamp *= 1000

        return timestamp

    def get_symbol_assets(self, symbol):
        base_asset, quote_asset = symbol.split(self._GLOBAL_SYMBOL_SEPARATOR)
        return base_asset, quote_asset

    def _init_session(self):
        session = requests.session()
        return session

    def _init_proxies(self):
        if self._PROXIES:
            self._session.proxies = self._PROXIES

    @staticmethod
    def _generate_timestamp():
        """
        Return a millisecond integer timestamp.
        """
        return int(time.time() * 1000)

    def _request(self, endpoint: str, method=None, signed=False, **kwargs):

        if signed and not self._API_KEY:
            raise ExchangeException("Authenticated endpoints require keys")

        if method is None:
            method = 'get'
        else:
            method = method.lower()

        # set default requests timeout
        kwargs['timeout'] = self._REQUESTS_TIMEOUT

        # add global requests params
        if self._REQUESTS_PARAMS:
            kwargs.update(self._REQUESTS_PARAMS)

        kwargs['params'] = kwargs.get('params', {})
        kwargs['headers'] = kwargs.get('headers', {})

        # timestamp
        timestamp = self._generate_timestamp()

        kwargs = self._handle_request_kwargs(kwargs, method, timestamp, endpoint, signed)

        uri = self._API_URL + endpoint

        response = getattr(self._session, method)(uri, **kwargs)
        return self._handle_response(response)

    def _handle_request_kwargs(self, kwargs, method, timestamp, endpoint, signed):
        return kwargs

    def _get(self, endpoint: str, signed=False, **kwargs):
        return self._request(endpoint, 'get', signed, **kwargs)

    def _post(self, endpoint: str, signed=False, **kwargs):
        return self._request(endpoint, 'post', signed, **kwargs)

    def _put(self, endpoint: str, signed=False, **kwargs):
        return self._request(endpoint, 'put', signed, **kwargs)

    def _delete(self, endpoint: str, signed=False, **kwargs):
        return self._request(endpoint, 'delete', signed, **kwargs)

    @staticmethod
    def _handle_response(response: requests.Response):

        if not (200 <= response.status_code < 300):
            raise ExchangeAPIException(f"Status code {response.status_code}. {response.text}")

        try:
            return response.json()
        except ValueError:
            raise ExchangeRequestException(f"Invalid Response: {response.text}")

    def _generate_hmac(self, signature_string) -> str:
        m = hmac.new(
            self._API_SECRET.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
            )
        return m.hexdigest()

    def _generate_query_string(self, params: dict) -> str:
        return '&'.join([f'{key}={value}' for key, value in params.items()])

    def _generate_signature(self, method, timestamp, path, params):
        query_string = self._generate_query_string(params)
        return self._generate_hmac(query_string)

    def _initialize(self):
        pass

    def update_headers(self, headers):
        self._session.headers.update(headers)

    @staticmethod
    def get_precision(value):
        return -int(math.log10(float(value))) if value else 0

    @staticmethod
    def truncate_value(value, precision):
        factor = 10 ** precision
        return math.trunc(value * factor) / factor

    @staticmethod
    def interval_to_minutes(interval):
        minutes_in_interval = {'1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '2h': 60*2, '4h': 60*4,
                               '6h': 60*6, '8h': 60*8, '12h': 60*12, '1d': 60*24, '1w': 60*24*7}
        if interval in minutes_in_interval:
            return minutes_in_interval[interval]
        else:
            raise ExchangeException(f"Unknown interval {interval}")

    def get_exchange_info(self, **kwargs):
        """
        'BTC/USDT': {
        'symbol': 'BTC/USDT',
        'original_symbol': 'BTCUSDT',
        'base_asset': 'BTC',
        'quote_asset': 'USDT',
        'status': 'TRADING',
        'price_precision': 1,
        'lot_precision': 3,
        'min_notional': 100.0
        },
        """
        raise NotImplementedException

    def get_tickers(self):
        """
        Retrieves tickers information.

        Returns:
        - dict: A dictionary with symbols as keys (e.g., 'BTC/USDT') and
          another dictionary as values, containing 'price' as float and
          'price_str' as str.

        Example:
        get_tickers()
        {
            'BTC/USDT': {'price': 100000, 'price_str': '100000'},
            'ETH/USDT': {'price': 50000, 'price_str': '50000'},
        }
        """
        raise NotImplementedException

    def get_ticker(self, symbol):
        """
        Retrieves symbol ticker information.

        Returns:
        - float, string: The symbol price and its string representation.

        Example:
        get_ticker(symbol='BTC/USDT')
        100000, '100000'
        """
        raise NotImplementedException

    def get_balances(self, **kwargs):
        """
        Retrieves the balance information.

        Returns:
        - dict: A dictionary with assets as keys (e.g., 'BTC') and
          another dictionary as values, containing 'total', 'free', and 'locked'
          balances (all floats).

        Example:
        get_balances()
        {
            'BTC': {'total': 0.2, 'free': 0.1, 'locked': 0.1},
            'ETH': {'total': 0.2, 'free': 0.1, 'locked': 0.1}
        }
        """
        raise NotImplementedException

    def get_order(self, order_id=None, symbol=None):
        raise NotImplementedException

    def get_orders(self, symbol: str, from_timestamp=None, **kwargs):
        raise NotImplementedException

    def get_open_orders(self, symbol: str):
        raise NotImplementedException

    def cancel_order(self, symbol=None, order_id=None):
        raise NotImplementedException

    def create_order(self, symbol, side, quantity, price=None, stop_price=None, type='LIMIT', time_in_force=None):
        raise NotImplementedException

    def get_klines(self, symbol, interval, from_timestamp=None, to_timestamp=None, limit=None):
        raise NotImplementedException

    def get_position_info(self, symbol):
        raise NotImplementedException

    def get_positions_info(self):
        raise NotImplementedException

    def change_margin_type(self, symbol, margin_type):
        raise NotImplementedException

    def change_leverage(self, symbol, leverage):
        raise NotImplementedException
