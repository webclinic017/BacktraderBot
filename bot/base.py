#!/usr/bin/env python3

from datetime import datetime
import backtrader as bt
from termcolor import colored
from bot.config import COIN_TARGET, COIN_REFER, ENV, PRODUCTION, DEBUG
from bot.utils import send_telegram_message
import itertools

LIMIT_ORDER_TIMEOUT_SECONDS = 20 * 60

class StrategyBase(bt.Strategy):

    def __init__(self):
        self.order = None
        self.last_operation = "SELL"
        self.status = "DISCONNECTED"
        self.bar_executed = 0
        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.curtradeid = -1
        self.log("Base strategy initialized")

    def notify_data(self, data, status, *args, **kwargs):
        self.status = data._getstatusname(status)
        self.log("!!! notify_data !!!")
        print(self.status)
        if status == data.LIVE:
            self.log("LIVE DATA - Ready to trade")

    def check_order_expired(self, order):
        result = False
        tstamp = order.ccxt_order['timestamp'] // 1000
        order_dt = datetime.fromtimestamp(tstamp)
        currdt = datetime.now()
        time_delta = currdt - order_dt
        if time_delta.total_seconds() >= LIMIT_ORDER_TIMEOUT_SECONDS:
            result = True

        return result

    def handle_pending_order(self, order):
        result = False
        self.log("An order is pending: order.ref={}, status={}".format(order.ref, order.status))
        # A limit order is pending
        # Check if the limit order has expired
        if self.check_order_expired(order):
            self.log("Limit order has expired after {} seconds. The order will be cancelled.".format(LIMIT_ORDER_TIMEOUT_SECONDS))
            self.broker.cancel(order)
            result = True
        return result

    def get_ticker(self, symbol):
        ticker_data = self.broker.fetch_ticker(symbol)
        return ticker_data

    def get_spread(self, ticker, significant_digits_num):
        bid_price = ticker['bid']
        ask_price = ticker['ask']
        return round(abs(bid_price - ask_price), significant_digits_num)

    def get_significant_digits_number(self, ticker):
        bid_signif_num = str(ticker['bid'])[::-1].find('.')
        ask_signif_num = str(ticker['ask'])[::-1].find('.')
        high_signif_num = str(ticker['high'])[::-1].find('.')
        low_signif_num = str(ticker['low'])[::-1].find('.')
        return max(bid_signif_num, ask_signif_num, high_signif_num, low_signif_num)

    def get_limit_price_order(self, ticker, is_long):
        price = ticker['bid'] if is_long is True else ticker['ask']
        significant_digits_num = self.get_significant_digits_number(ticker)
        spread = self.get_spread(ticker, significant_digits_num)
        min_tick_price = round(pow(10, -significant_digits_num), significant_digits_num)
        if spread == min_tick_price:
            adj_tick_price = min_tick_price
        else:
            adj_tick_price = -min_tick_price  # If spread is large then would try to insert an order in order book at the first place
        if is_long is True:
            adj_tick_price *= -1
        self.log("adjusted_tick_price: {:.8f}".format(adj_tick_price))
        return round(price + adj_tick_price, significant_digits_num)

    def long(self):
        if self.last_operation == "BUY":
            return

        amount = 33 #0.004
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        price = self.get_limit_price_order(ticker, True)
        self.curtradeid = next(self.tradeid)
        self.log("BUY order submitted: Symbol={}, Amount={}, Price={}, TradeId={}".format(self.data.symbol, amount, price, self.curtradeid))
        return self.buy(size=amount, price=price, exectype=bt.Order.Limit, tradeid=self.curtradeid, params={"type": "limit"})

    def short(self):
        if self.last_operation == "SELL":
            return

        amount = 33 #0.004
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        price = self.get_limit_price_order(ticker, False)
        self.log("SELL order submitted: Symbol={}, Amount={}, Price={}, TradeId={}".format(self.data.symbol, amount, price, self.curtradeid))
        #return self.sell(size=amount, price=price, exectype=bt.Order.Limit, tradeid=self.curtradeid, params={"type": "limit"})
        return self.close(tradeid=self.curtradeid, params={"type": "market"})

    def notify_order(self, order):
        self.log("!!!!!! notify_order(): order.status={}, order={}, order.created={}, order.executed={}".format(order.status, vars(order), vars(order.created), vars(order.executed)))

        if order.status in [order.Created, order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log('ORDER CREATED/ACCEPTED/SUBMITTED')
            self.order = order
            return

        if order.status in [order.Expired]:
            self.log('BUY EXPIRED')

        elif order.status in [order.Completed]:
            if order.isbuy():
                self.last_operation = "BUY"
                self.log(
                    'BUY EXECUTED, Price: %.8f, Cost: %.8f, Comm %.8f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

            else:  # Sell
                self.last_operation = "SELL"
                self.log('SELL EXECUTED, Price: %.8f, Cost: %.8f, Comm %.8f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            # Sentinel to None: new orders allowed
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected: Status %s - %s' % (order.Status[order.status],
                                                                         self.last_operation))

        self.order = None

    def notify_trade(self, trade):
        self.log("!!!!! notify_trade(): trade={}".format(vars(trade)))
        if not trade.isclosed:
            return

        color = 'green'
        if trade.pnl < 0:
            color = 'red'

        self.log(colored('OPERATION PROFIT, GROSS %.8f, NET %.8f' % (trade.pnl, trade.pnlcomm), color))

    def log(self, txt, color=None):
        if not DEBUG:
            return

        value = datetime.now()

        if color:
            txt = colored(txt, color)

        print('[%s] %s' % (value, txt))
        send_telegram = False
        if send_telegram:
            send_telegram_message(txt)
