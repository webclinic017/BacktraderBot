from datetime import datetime
from bot.config.bot_config import BotConfig


class LiveTradingProcessor(object):

    def __init__(self, broker, data, debug):
        self.broker = broker
        self.data = data
        self.debug = debug

    def log(self, txt, dt=None):
        if self.debug:
            dt = dt or self.data.datetime.datetime()
            print('%s  %s' % (dt, txt))

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
