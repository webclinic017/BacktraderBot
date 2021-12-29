import backtrader as bt
from datetime import datetime
from bot.config.bot_config import BotConfig
from bot.utils import send_telegram_message
from bot.config.bot_strategy_config import BotStrategyConfig
from strategies.processors.strategyprocessor import BaseStrategyProcessor
from common.constants import *


class LiveTradingStrategyProcessor(BaseStrategyProcessor):

    def __init__(self, strategy, debug):
        super().__init__(strategy, debug)
        self.strategy = strategy
        self.broker = strategy.broker
        self.analyzers = strategy.analyzers
        self.data = strategy.data
        self.debug = debug

    def log(self, txt, send_telegram_flag=False):
        if not self.debug:
            return

        timestamp = datetime.now()

        log_text = '[{}] {}'.format(timestamp, txt)
        print(log_text)
        send_telegram_cfg = BotConfig.get_send_to_telegram()
        if send_telegram_flag is True and send_telegram_cfg is True:
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
            self.log("**** Started {} in LIVE mode: {} ****".format(BotStrategyConfig.get_instance().botid.upper(), self.data.symbol), True)
            self.log("=" * 120)
            self.log("LIVE DATA - Ready to trade")
            self.log("=" * 120)

    def notify_analyzers(self):
        pass

    def get_order_size(self, data=None, is_long=None):
        return BotStrategyConfig.get_instance().order_size

    def get_exchange_size(self, ticker, size_quote_curr):
        #self.broker.store.exchange.verbose = True
        if self.broker.store.exchange.id == BINANCE_EXCHANGE:
            last_price = ticker["last"]
            return round(size_quote_curr / last_price)
        else:
            return size_quote_curr

    def open_long_position(self, size=None):
        size = self.get_order_size() if not size else size
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        exch_size = self.get_exchange_size(ticker, size)
        order = self.strategy.generic_buy(tradeid=self.strategy.curtradeid, size=exch_size, exectype=bt.Order.Market, params={})
        self.log("BUY MARKET base order submitted: Symbol={}, Size={}, curtradeid={}, order.ref={}".format(self.data.symbol, size, self.strategy.curtradeid, order.ref), True)
        return order

    def open_short_position(self, size=None):
        size = self.get_order_size() if not size else size
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        exch_size = self.get_exchange_size(ticker, size)
        order = self.strategy.generic_sell(tradeid=self.strategy.curtradeid, size=exch_size, exectype=bt.Order.Market, params={})
        self.log("SELL MARKET base order submitted: Symbol={}, Size={}, curtradeid={}, order.ref={}".format(self.data.symbol, size, self.strategy.curtradeid, order.ref), True)
        return order

    def close_position(self):
        order = self.strategy.generic_close(tradeid=self.strategy.curtradeid, params={})
        self.log("Closed position by MARKET order: Symbol={}, curtradeid={}, order.ref={}".format(self.data.symbol, self.strategy.curtradeid, order.ref), True)
        return order
