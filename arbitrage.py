
import ccxt
import datetime
import time
import math
# import pandas as pd
import numpy as np
import pprint

# ==== Initial exchange parameters =====
symbol = str('BTC/USD')
symbol_list = ['BTC/USD', 'ETH/USD']  # === Define This ===

# ==== Initial trade parameters =====
expiry = 'this_month'               # === 'this_week','this_month','this_quarter' ===
reqd_spread_percent = 0.02          # === Custom spread % --> Default = 2%
closeout_spread_percent = 0.0025    # === Closeout Spread % --> Default = 0.25%

reqd_balance = 100                  # === Dollar Amount deposited in each exchange ===
# =========== Define these above parameters =================

# =========== Define Exchanges ==============
exchange_id1 = 'okex'       # === Define First Exchange ===
exchange_class1 = getattr(ccxt, exchange_id1)
exchange1 = exchange_class1({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'timeout': 30000,
    'enableRateLimit': True,
})

exchange_id2 = 'deribit'    # === Define Second Exchange ===
exchange_class2 = getattr(ccxt, exchange_id2)
exchange2 = exchange_class2({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'timeout': 30000,
    'enableRateLimit': True,
})

# ===== Run the different functions in arbitrage bot =====
def main():
    while exchange1.fetch_balance() > reqd_balance and exchange2.fetch_balance() > reqd_balance:
        for sym in symbol_list:
            initiate_arbitrage(sym, expiry=expiry)
            closeout_arbitrage(sym, expiry=expiry)
            trade_details(sym)
            check_openorders(sym)
            exchange_balances()
    time.sleep(20)

# ===== Visualise market depth =====
def order_book(exchange, symbol, limit):
    exchange = getattr(ccxt, exchange)()
    exchange.load_markets()
    data = exchange.fetch_order_book(symbol,limit)
    bid = data['bids'][0][0] if len(data['bids']) > 0 else None
    ask = data['asks'][0][0] if len(data['asks']) > 0 else None
    return bid, ask

# ====== Get Bid and Ask prices for both Exchanges ======
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


# ========= Defining the order quantity at the beginning ================
# This same order qty has to be used when closing out arbitrage

def orderqty(symbol, expiry):
    bid_exch1, ask_exch1, bid_exch2, ask_exch2 = get_prices(symbol, expiry)
    avg_price = (bid_exch1 + ask_exch1 + bid_exch2 + ask_exch2)/4

    order_qty = reqd_balance/avg_price
    return order_qty

order_qty = orderqty(symbol,expiry)

# ===== Function to initiate arbitrage position based on a defined spread % =====
def initiate_arbitrage(symbol, expiry):
    # Initialize buy order and sell order price
    buy_order_price = 0.0
    sell_order_price = 0.0

    buy_order = dict()
    sell_order = dict()

    bid_exch1, ask_exch1, bid_exch2, ask_exch2 = get_prices(symbol, expiry)

    # Sell Exchange1 Buy Exchange2
    spread1 = bid_exch1 - ask_exch2
    print ("Sell Exchange1 Buy Exchange2 - Spread:", spread1)

    # Sell Exchange2 Buy Exchange1
    spread2 = bid_exch2 - ask_exch1
    print ("Sell Exchange1 Buy Exchange2 - Spread:", spread2)

    # ===== Arbitrage condition and calculation =====
    # only initiate position if none exists
    while (len(exchange1.future_position()) == 0 and len(exchange2.future_position())) == 0:
        if (spread1 > 0) and spread1 > reqd_spread_percent * (bid_exch1 + ask_exch1)/2:
            buy_order_price = ask_exch2
            # === Question is whether we want to create a market order or a Limit order ===
            buy_order = exchange2.create_market_buy_order(symbol,
                                                          order_qty,
                                                          {'trading_agreement': 'agree'})
            sell_order_price = bid_exch1
            sell_order = exchange1.create_market_sell_order(symbol,
                                                            order_qty,
                                                            {'trading_agreement': 'agree'})

        elif (spread2 > 0) and spread2 > reqd_spread_percent * (bid_exch2 + ask_exch2)/2:
            buy_order_price = ask_exch1
            buy_order = exchange1.create_market_buy_order(symbol,
                                                          order_qty,
                                                          {'trading_agreement': 'agree'})

            sell_order_price = bid_exch2
            sell_order = exchange2.create_market_sell_order(symbol,
                                                            order_qty,
                                                            {'trading_agreement': 'agree'})

    captured_spread = sell_order_price - buy_order_price

    print('Buy Order Price:', buy_order_price)
    print('Sell Order Price:', sell_order_price)
    print('Captured Spread:', captured_spread)

    return buy_order_price, buy_order, sell_order_price, sell_order, captured_spread


# ===== Close arbitrage position once spread percent falls below certain value ======
def closeout_arbitrage(symbol, expiry):
    buy_close_price = 0.0
    sell_close_price = 0.0

    buy_price, buyorder, sell_price, sellorder, current_spread = initiate_arbitrage(symbol, expiry)

    bid_exch1, ask_exch1, bid_exch2, ask_exch2 = get_prices(symbol, expiry)

    # ===== Arbitrage condition and calculation =====
    # ===== Only initiate position if none exists ===
    while (len(exchange1.future_position()) > 0 and len(exchange2.future_position())) > 0:
        if current_spread < closeout_spread_percent * (buy_price + sell_price) / 2:
            buy_close_price = ask_exch2
            exchange2.create_market_buy_order(symbol,
                                              order_qty,
                                              {'trading_agreement': 'agree'})
            sell_close_price = bid_exch1
            exchange1.create_market_sell_order(symbol,
                                               order_qty,
                                               {'trading_agreement': 'agree'})
        else:
            sell_close_price = bid_exch2
            exchange2.create_market_sell_order(symbol,
                                               order_qty,
                                               {'trading_agreement': 'agree'})
            buy_close_price = ask_exch1
            exchange1.create_market_buy_order(symbol,
                                              order_qty,
                                              {'trading_agreement': 'agree'})

    closeout_spread = sell_close_price - buy_close_price

    print('Buy Order Price:', buy_close_price)
    print('Sell Order Price:', sell_close_price)

    return buy_close_price, sell_close_price, closeout_spread


def check_openorders(symbol):
    if exchange1.has['fetch_open_orders']:
        exch1_open_orders = exchange1.fetch_open_orders(symbol)

    if exchange2.has['fetch_open_orders']:
        exch2_open_orders = exchange2.fetch_open_orders(symbol)

    # If Open orders exist, First Cancel and then create new Market Order
    while len(exchange1.fetch_open_orders(symbol)) > 0:
        for idd in exchange1.fetch_open_orders(symbol)['id']:
            try:
                # Cancel the open order and create a new market order
                exchange1.cancel_order(str(idd))
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
    while len(exchange2.fetch_open_orders(symbol)) > 0:
        for idd in exchange2.fetch_open_orders(symbol)['id']:
            try:
                exchange2.cancel_order(str(idd))
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
    print(exchange_id1 + ' Closed Orders:',
          exchange1.fetch_closed_orders(symbol))
    print(exchange_id2 + ' Closed Orders:',
          exchange2.fetch_closed_orders(symbol))

    print("Open Orders:")
    print(exchange_id1 + ' Open Orders:',
          exchange1.fetch_open_orders(symbol))
    print(exchange_id2 + ' Open Orders:',
          exchange2.fetch_open_orders(symbol))

    print 'Getting Exchange Positions ...\n'
    print(exchange_id1 + ' Exchange Positions:',
          exchange1.private_post_positions(symbol))
    print(exchange_id2 + ' Exchange Positions:',
          exchange2.private_post_positions(symbol))

# ========= Get Balance amounts left on each exchange ==========
def exchange_balances():
    print exchange_id1 + ' Balance:\n', exchange1.fetch_balance()
    print exchange_id2 + ' Balance:\n', exchange2.fetch_balance()

if __name__ == "__main__":
    main()





