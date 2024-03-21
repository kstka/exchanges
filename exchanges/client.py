from exchanges.exceptions import ExchangeException
from exchanges.binance import Binance
from exchanges.kucoin import KuCoin
from exchanges.bybit import ByBit


class Client:

    def __init__(self,
                 exchange_name: str,
                 api_key=None,
                 api_secret=None,
                 api_password=None,
                 futures=False,
                 proxies=None,
                 requests_params=None,
                 requests_timeout=10):

        if exchange_name == 'binance':
            self._exchange = self.binance(api_key=api_key, api_secret=api_secret, proxies=proxies, futures=futures,
                                          requests_params=requests_params, requests_timeout=requests_timeout)
        elif exchange_name == 'kucoin':
            self._exchange = self.kucoin(api_key=api_key, api_secret=api_secret, api_password=api_password,
                                         futures=futures, proxies=proxies,
                                         requests_params=requests_params, requests_timeout=requests_timeout)
        elif exchange_name == 'bybit':
            self._exchange = self.bybit(api_key=api_key, api_secret=api_secret, proxies=proxies, futures=futures,
                                        requests_params=requests_params, requests_timeout=requests_timeout)
        else:
            raise ExchangeException(f"Unknown exchange name {exchange_name}")

    @staticmethod
    def binance(**kwargs):
        return Binance(**kwargs)

    @staticmethod
    def kucoin(**kwargs):
        return KuCoin(**kwargs)

    @staticmethod
    def bybit(**kwargs):
        return ByBit(**kwargs)

    def get_exchange(self):
        return self._exchange
