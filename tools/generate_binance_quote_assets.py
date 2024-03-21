from exchanges import Binance


def main():

    for futures in [False, True]:
        quote_assets = set()

        client = Binance(futures=futures)

        exchange_info = client.get_exchange_info()
        for symbol, info in exchange_info.items():
            quote_assets.add(info['quote_asset'])

        market = 'Spot' if not futures else 'Futures'
        print(f'Binance {market} quote assets: {quote_assets}')


if __name__ == '__main__':
    main()
