from abc import abstractmethod
from strategies.managers.stoplossmanager import StopLossManager
from strategies.managers.takeprofitmanager import TakeProfitManager
from strategies.managers.trailingbuymanager import TrailingBuyManager
from strategies.managers.dcamodemanager import DcaModeManager


class BaseStrategyProcessor(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.debug = debug
        self.stoplossmanager = StopLossManager(strategy, self, debug)
        self.takeprofitmanager = TakeProfitManager(strategy, self, debug)
        self.trailingbuymanager = TrailingBuyManager(strategy, self, debug)
        self.dcamodemanager = DcaModeManager(strategy, self, debug)

    def on_open_position_trade_managers(self, pos_price, is_long):
        self.stoplossmanager.activate(pos_price, is_long)
        self.takeprofitmanager.activate(pos_price, is_long)

    def on_next_trade_managers(self):
        sl_result = self.stoplossmanager.on_next()
        tp_result = self.takeprofitmanager.on_next()
        # OCO functionality
        if sl_result and not tp_result:
            self.takeprofitmanager.deactivate()
        if not sl_result and tp_result:
            self.stoplossmanager.deactivate()

        return sl_result or tp_result

    def on_close_position_trade_managers(self):
        self.stoplossmanager.deactivate()
        self.takeprofitmanager.deactivate()

    @abstractmethod
    def log(self, txt, send_telegram_flag=False):
        pass

    @abstractmethod
    def check_order_expired(self, order):
        pass

    @abstractmethod
    def get_ticker(self, symbol):
        pass

    @abstractmethod
    def get_spread(self, ticker, significant_digits_num):
        pass

    @abstractmethod
    def get_significant_digits_number(self, ticker):
        pass

    @abstractmethod
    def get_limit_price_order(self, ticker, is_long):
        pass

    @abstractmethod
    def set_startcash(self, startcash):
        pass

    @abstractmethod
    def notify_data(self, data, status, *args, **kwargs):
        pass

    @abstractmethod
    def notify_analyzers(self):
        pass

    @abstractmethod
    def get_order_size(self):
        pass

    @abstractmethod
    def open_long_position(self):
        pass

    @abstractmethod
    def open_short_position(self):
        pass

    @abstractmethod
    def close_position(self):
        pass