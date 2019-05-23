import backtrader as bt
from datetime import datetime
from bot.config.bot_config import BotConfig
from termcolor import colored
from bot.utils import send_telegram_message
from bot.config.bot_strategy_config import BotStrategyConfig


class LiveTradingStrategyProcessor(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.broker = strategy.broker
        self.analyzers = strategy.analyzers
        self.data = strategy.data
        self.debug = debug

    def log(self, txt, color=None):
        if not self.debug:
            return

        value = datetime.now()

        if color:
            txt = colored(txt, color)

        print('[%s] %s' % (value, txt))
        send_telegram = BotConfig.get_send_to_telegram()
        if send_telegram:
            send_telegram_message(txt)

    def check_order_expired(self, order):
        result = False
        tstamp = order.ccxt_order['timestamp'] // 1000
        order_dt = datetime.fromtimestamp(tstamp)
        currdt = datetime.now()
        time_delta = currdt - order_dt
        if time_delta.total_seconds() >= BotConfig.get_limit_order_timeout_seconds():
            result = True

        return result

    def handle_pending_order(self, order):
        result = False
        self.log("An order is pending: order.ref={}, status={}".format(order.ref, order.status))
        # A limit order is pending
        # Check if the limit order has expired
        if self.check_order_expired(order):
            self.log("Limit order has expired after {} seconds. The order will be cancelled.".format(BotConfig.get_limit_order_timeout_seconds()))
            self.broker.cancel(order)
            self.strategy.curr_position = 0
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
        return max(bid_signif_num, ask_signif_num)

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

    def set_startcash(self, startcash):
        pass
        #self.broker.setcash(startcash)

    def notify_data(self, data, status, *args, **kwargs):
        self.strategy.status = self.strategy.data._getstatusname(status)
        self.log("notify_data - status={}".format(self.strategy.status))
        if status == data.LIVE:
            self.log("=" * 120)
            self.log("LIVE DATA - Ready to trade")
            self.log("=" * 120)

    def notify_analyzers(self):
        pass

    def get_order_size(self):
        return BotStrategyConfig.get_instance().order_size

    def buy(self):
        amount = self.get_order_size()
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        price = self.get_limit_price_order(ticker, True)
        order = self.strategy.buy(size=amount, price=price, exectype=bt.Order.Limit, tradeid=self.strategy.curtradeid, params={"type": "limit"})
        self.log("BUY LIMIT order submitted: Symbol={}, Amount={}, Price={}, curtradeid={}, order.ref={}".format(self.data.symbol, amount, price, self.strategy.curtradeid, order.ref))
        return order

    def sell(self):
        amount = self.get_order_size()
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        price = self.get_limit_price_order(ticker, False)
        order = self.strategy.sell(size=amount, price=price, exectype=bt.Order.Limit, tradeid=self.strategy.curtradeid, params={"type": "limit"})
        self.log("SELL LIMIT order submitted: Symbol={}, Amount={}, Price={}, curtradeid={}, order.ref={}".format(self.data.symbol, amount, price, self.strategy.curtradeid, order.ref))
        return order

    def close(self):
        order = self.strategy.close(tradeid=self.strategy.curtradeid, params={"type": "market"})
        self.log("Closing open position by MARKET order: Symbol={}, curtradeid={}, order.ref={}".format(self.data.symbol, self.strategy.curtradeid, order.ref))
        return order
