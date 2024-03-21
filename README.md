# Exchanges

Welcome to the Exchanges, a Python package designed to streamline the process of interfacing with various cryptocurrency exchanges via their APIs. This tool is primarily developed for personal use, aiming to simplify the integration and interaction with exchange platforms for automated trading bots and financial analysis tools.

This package is under development for personal projects and, due to time constraints, may have incomplete documentation or descriptions for some methods. The current version includes only those API endpoints that are utilized in my trading robots, making it less comprehensive than a full-fledged library for interacting with cryptocurrency exchanges. However, the included functionality should serve as a solid foundation for those with similar needs, offering a starting point for expansion.

# Features

* Unified API Access: Simplify your codebase by using a single, unified interface to interact with multiple cryptocurrency exchanges.
* Extensible: Designed with extensibility in mind. New exchanges and endpoints can be added easily, following the patterns established by the existing codebase.

# Currently supported exchanges

* Binance
* KuCoin
* ByBit

# Getting Started
To get started with Exchanges, clone the repository and install the package using pip:

```
git clone https://github.com/kstka/exchanges
cd exchanges
pip install .
```

# Example usage

Selecting exchange from a string
```python
from exchanges import Client

EXCHANGE_NAME = 'kucoin'
API_KEY = ''
API_SECRET = ''

client = Client(EXCHANGE_NAME, API_KEY, API_SECRET)
client = client.get_exchange()

print(client.get_exchange_info())
```  

Selecting exchange from a class
```python
from exchanges import ByBit

API_KEY = ''
API_SECRET = ''

client = ByBit(API_KEY, API_SECRET)

print(client.get_exchange_info())
```

# License
Exchanges is available under the MIT License.