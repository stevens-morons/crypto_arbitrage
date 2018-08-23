import ccxt
import datetime
import time
import math
# import pandas as pd
import numpy as np
import pprint

# ==== Initial Parameters =====
symbol = str('BTC/USD')
symbol_list = ['BTC/USD','ETH/USD']
timeframe = str('1d')
# exchange = str('okex')
start_date = str('2018-01-01')
get_data = True
order_qty = 1.0

expiry = 'this_month'    # === 'this_week','this_month','this_quarter' ===
reqd_spread = 0.05       # Custom spread % based on a suitably divergent level
closeout_spread = 0.005  # Spread % at which position is closed out

# ==== from variable id ====
exchange_id1 = 'okex'
exchange_class1 = getattr(ccxt, exchange_id1)
exchange1 = exchange_class1({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'timeout': 30000,
    'enableRateLimit': True,
})

exchange_id2 = 'deribit'
exchange_class2 = getattr(ccxt, exchange_id2)
exchange2 = exchange_class2({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'timeout': 30000,
    'enableRateLimit': True,
})

# ===== Run the different functions in arbitrage bot =====
def main():
    #Set Initial conditions for bot
    for sym in symbol_list:
        initiate_arbitrage(sym,expiry=expiry)
        check_openorders(sym)
    time.sleep(20)


def order_book(exchange,symbol,limit):
    exchange = getattr(ccxt, exchange)()
    exchange.load_markets()
    data = exchange.fetch_order_book(symbol,limit)
    bid = data['bids'][0][0] if len(data['bids']) > 0 else None
    ask = data['asks'][0][0] if len(data['asks']) > 0 else None
    return bid, ask


def get_prices(symbol, expiry):

    print("Getting Order Book for OKEX:")
    # Get Order Book for First exchange
    orderbook_exch1 = exchange1.fetch_order_book(symbol, 5, {'contract_type': expiry})

    # get bid and ask prices for First Exchange
    bid_exch1 = orderbook_exch1['bids'][0][0] if len(orderbook_exch1['bids']) > 0 else None
    ask_exch1 = orderbook_exch1['asks'][0][0] if len(orderbook_exch1['asks']) > 0 else None

    print("Getting Order Book for Deribit:")
    # Get Order Book for Second exchange
    orderbook_exch2 = exchange2.fetch_order_book(symbol, 5, {'contract_type': expiry})

    # get bid and ask prices for Second Exchange
    bid_exch2 = orderbook_exch2['bids'][0][0] if len(orderbook_exch2['bids']) > 0 else None
    ask_exch2 = orderbook_exch2['asks'][0][0] if len(orderbook_exch2['asks']) > 0 else None

    return bid_exch1, ask_exch1, bid_exch2, ask_exch2


# Function to initiate arbitrage position based on a defined spread %
def initiate_arbitrage(symbol,expiry):
    # Initialize buy order and sell order price
    buy_order_price = 0.0
    sell_order_price = 0.0

    bid_exch1, ask_exch1, bid_exch2, ask_exch2 = get_prices(symbol,expiry)
    # Sell Exchange1 Buy Exchange2
    spread1 = bid_exch1 - ask_exch2
    print ("Sell Exchange1 Buy Exchange2 - Spread:", spread1)

    # Sell Exchange2 Buy Exchange1
    spread2 = bid_exch2 - ask_exch1
    print ("Sell Exchange1 Buy Exchange2 - Spread:", spread2)

    # ===== Arbitrage condition and calculation =====
    # only initiate position if none exists
    while (exchange1.future_position() == 0) and (exchange2.future_position() == 0):
        if (spread1 > spread2) and spread1 > reqd_spread * (bid_exch1 + ask_exch1)/2:
            buy_order_price = ask_exch2
            exchange2.create_market_buy_order(symbol,
                                              order_qty,
                                              {'trading_agreement': 'agree'})
            sell_order_price = bid_exch1
            exchange1.create_market_sell_order(symbol,
                                               order_qty,
                                               {'trading_agreement': 'agree'})

        elif (spread2 > spread1) and spread2 > reqd_spread * (bid_exch2 + ask_exch2)/2:
            buy_order_price = ask_exch1
            exchange1.create_market_buy_order(symbol,
                                              order_qty,
                                              {'trading_agreement': 'agree'})

            sell_order_price = bid_exch2
            exchange2.create_market_sell_order(symbol,
                                               order_qty,
                                               {'trading_agreement': 'agree'})

    captured_spread = sell_order_price - buy_order_price

    print('Buy Order Price:', buy_order_price)
    print('Sell Order Price:', sell_order_price)

    return buy_order_price, sell_order_price, captured_spread


def closeout_arbitrage(symbol,expiry):
    buy_order_price = 0.0
    sell_order_price = 0.0

    bid_exch1, ask_exch1, bid_exch2, ask_exch2 = get_prices(symbol, expiry)
    # Sell Exchange1 Buy Exchange2
    spread1 = bid_exch1 - ask_exch2
    print ("Sell Exchange1 Buy Exchange2 - Spread:", spread1)

    # Sell Exchange2 Buy Exchange1
    spread2 = bid_exch2 - ask_exch1
    print ("Sell Exchange1 Buy Exchange2 - Spread:", spread2)

    # ===== Arbitrage condition and calculation =====
    # only initiate position if none exists
    while (exchange1.future_position() == 1) and (exchange2.future_position() == 1):
        if (spread1 > spread2) and spread1 > reqd_spread * (bid_exch1 + ask_exch1) / 2:
            buy_order_price = ask_exch2
            exchange2.create_market_buy_order(symbol,
                                              order_qty,
                                              {'trading_agreement': 'agree'})
            sell_order_price = bid_exch1
            exchange1.create_market_sell_order(symbol,
                                               order_qty,
                                               {'trading_agreement': 'agree'})

        elif (spread2 > spread1) and spread2 > reqd_spread * (bid_exch2 + ask_exch2) / 2:
            buy_order_price = ask_exch1
            exchange1.create_market_buy_order(symbol,
                                              order_qty,
                                              {'trading_agreement': 'agree'})

            sell_order_price = bid_exch2
            exchange2.create_market_sell_order(symbol,
                                               order_qty,
                                               {'trading_agreement': 'agree'})

    captured_spread = sell_order_price - buy_order_price

    print('Buy Order Price:', buy_order_price)
    print('Sell Order Price:', sell_order_price)

    return buy_order_price, sell_order_price, captured_spread


def check_openorders(symbol):
    if exchange1.has['fetch_open_orders']:
        exchange1.fetch_open_orders(symbol)

    # If Open orders exist, First Cancel and then create new Market Order
    while exchange1.fetch_open_orders(symbol)['status'] == 'open':
        try:
            # Cancel the open order and create a new market order
            exchange1.cancel_order(str(exchange1.fetch_open_orders(symbol)['id']))
            # Since order is canceled, a new market order has to be created which
            # matches the 'side'(buy/sell)
            if exchange1.fetch_open_orders(symbol)['side'] == 'buy':
                exchange1.create_market_buy_order(symbol,
                                                  order_qty,
                                                  {'trading_agreement': 'agree'})
            else:
                exchange1.create_market_sell_order(symbol,
                                                   order_qty,
                                                   {'trading_agreement': 'agree'})

        except 'NetworkError':
            print 'Network Error'

        except 'ExchangeError':
            print 'Exchange Error'

    # If Open orders exist, First Cancel and then create new Market Order
    while exchange2.fetch_open_orders(symbol)['status'] == 'open':
        try:
            exchange2.cancel_order(str(exchange2.fetch_open_orders(symbol)['id']))
            # Since order is canceled, a new market order has to be created which
            # matches the 'side'(buy/sell)
            if exchange2.fetch_open_orders(symbol)['side'] == 'buy':
                exchange2.create_market_buy_order(symbol,
                                                  order_qty,
                                                  {'trading_agreement': 'agree'})
            else:
                exchange2.create_market_sell_order(symbol,
                                                   order_qty,
                                                   {'trading_agreement': 'agree'})
        except 'NetworkError':
            print 'Network Error'

        except 'ExchangeError':
            print 'Exchange Error'


# ======== Details of Open & Closed Trades =========
def trade_details(symbol):
    print("Closed Orders:")
    pprint.pprint(exchange1.fetch_closed_orders(symbol))
    pprint.pprint(exchange2.fetch_closed_orders(symbol))

    print("Open Orders:")
    pprint.pprint(exchange1.fetch_open_orders(symbol))
    pprint.pprint(exchange2.fetch_open_orders(symbol))

    print("My Trades:")
    pprint.pprint(exchange1.fetch_my_trades(symbol))
    pprint.pprint(exchange1.fetch_my_trades(symbol))


if __name__ == "__main__":
    main()
