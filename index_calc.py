import ccxt
import datetime
import time
import math
import pandas as pd
import numpy as np
from pprint import pprint
# from historical_data import to_unix_time

symbol = 'BTC/USD'
timeframe = '1ms'
since = '2017-01-01 00:00:00'
limit = 5

# hist_start_date = int(to_unix_time(since))

def exchange_price(exchange,symbol,limit):
    exchange = getattr(ccxt, exchange)()
    exchange.load_markets()
    data = exchange.fetch_order_book(symbol,limit)
    bid = data['bids'][0][0] if len(data['bids']) > 0 else None
    ask = data['asks'][0][0] if len(data['asks']) > 0 else None
    mid = (bid+ask)/2
    return mid

# ===
def deribit_index(symbol):
    kraken_price = exchange_price('kraken',symbol,5)
    itbit_price = exchange_price('itbit',symbol,5)
    gemini_price = exchange_price('itbit',symbol,5)
    gdax_price = exchange_price('gdax',symbol,5)
    bitstamp_price = exchange_price('bitstamp',symbol,5)
    bitfinex_price = exchange_price('bitfinex',symbol,5)

    list = [kraken_price,itbit_price,gemini_price,gdax_price,bitstamp_price,bitfinex_price]
    sorted_list = list.sort()
    deri_index = (sorted_list[1]+sorted_list[2]+sorted_list[3]+sorted_list[4])/4
    return deri_index


def okex_index(symbol):
    kraken_price = exchange_price('kraken', symbol, 5)
    gemini_price = exchange_price('itbit', symbol, 5)
    gdax_price = exchange_price('gdax', symbol, 5)
    bitstamp_price = exchange_price('bitstamp', symbol, 5)
    bitfinex_price = exchange_price('bitfinex', symbol, 5)

    ok_index = (kraken_price + gemini_price + gdax_price + bitstamp_price + bitfinex_price)/5

    return ok_index

print("Deribit BTC Index:",deribit_index('BTC/USD'))
print("OKEX BTC Index:",okex_index('BTC/USD'))
