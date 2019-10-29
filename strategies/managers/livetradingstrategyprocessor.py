import backtrader as bt
from datetime import datetime
from bot.config.bot_config import BotConfig
from bot.utils import send_telegram_message
from bot.config.bot_strategy_config import BotStrategyConfig
from .strategyprocessor import BaseStrategyProcessor


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

    def get_order_size(self):
        return BotStrategyConfig.get_instance().order_size

    def open_long_position(self):
        size = self.get_order_size()
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        order = self.strategy.generic_buy(tradeid=self.strategy.curtradeid, size=size, exectype=bt.Order.Market, params={"type": "market"})
        self.log("BUY MARKET base order submitted: Symbol={}, Size={}, curtradeid={}, order.ref={}".format(self.data.symbol, size, self.strategy.curtradeid, order.ref), True)
        return order

    def open_short_position(self):
        size = self.get_order_size()
        ticker = self.get_ticker(self.data.symbol)
        self.log("Last ticker data: {}".format(ticker))
        order = self.strategy.generic_sell(tradeid=self.strategy.curtradeid, size=size, exectype=bt.Order.Market, params={"type": "market"})
        self.log("SELL MARKET base order submitted: Symbol={}, Size={}, curtradeid={}, order.ref={}".format(self.data.symbol, size, self.strategy.curtradeid, order.ref), True)
        return order

    def close_position(self):
        order = self.strategy.generic_close(tradeid=self.strategy.curtradeid, params={"type": "market"})
        self.log("Closed position by MARKET order: Symbol={}, curtradeid={}, order.ref={}".format(self.data.symbol, self.strategy.curtradeid, order.ref), True)
        return order
