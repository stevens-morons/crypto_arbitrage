# Code to download Historical data from any cryptocurrency
# exchange

import ccxt
import datetime
import time
import math
import pandas as pd
import numpy as np

symbol = 'BTC/USD'
timeframe = '1d'
since = '2017-01-01 00:00:00'


def to_unix_time(timestamp):
    epoch = datetime.datetime.utcfromtimestamp(0)  # start of epoch time
    my_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    diff = my_time - epoch
    return diff.total_seconds() * 1000

hist_start_date = int(to_unix_time(since))

# Function for Exchange Info
def exchange_data(exchange,symbol,timeframe,since):
    exchange = getattr(ccxt, exchange)()
    exchange.load_markets()
    data = exchange.fetch_ohlcv(symbol,timeframe,since)
    return data

def csv_filename(symbol,exchange):
    # Csv File Name
    symbol_out = symbol.replace("/", "")
    filename = '{}-{}-{}.csv'.format(exchange, symbol_out, timeframe)
    return filename

# Function to write csv file
header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']

def write_to_csv(data,symbol,exchange):

    df = pd.DataFrame(data, columns=header)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df['Timestamp'] = df['Timestamp'].dt.strftime('%Y%m%d %H%M')
    df[['Volume']] = df[['Volume']].astype(int)

    tocsv = df.to_csv(csv_filename(symbol,exchange), index=False, header=False, sep=';')
    return tocsv

# ====== Calling the functions ======
kraken = exchange_data('kraken','BTC/USD',timeframe=timeframe,since=hist_start_date)
write_to_csv(kraken,'BTC/USD','kraken')
