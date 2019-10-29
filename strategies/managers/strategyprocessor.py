from abc import abstractmethod
from strategies.managers.stoplossmanager import StopLossManager
from strategies.managers.takeprofitmanager import TakeProfitManager
from strategies.managers.trailingbuymanager import TrailingBuyManager
from strategies.managers.dcamodemanager import DcaModeManager


class BaseStrategyProcessor(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.debug = debug
        self.stoplossmanager = StopLossManager(strategy, debug)
        self.takeprofitmanager = TakeProfitManager(strategy, debug)
        self.trailingbuymanager = TrailingBuyManager(strategy, debug)
        self.dcamodemanager = DcaModeManager(strategy, debug)

    def on_open_position_trade_managers(self, tradeid, pos_price, pos_size, is_long):
        self.stoplossmanager.activate(tradeid, pos_price, pos_size, is_long)
        self.takeprofitmanager.activate(tradeid, pos_price, pos_size, is_long)

    def on_next_trade_managers(self):
        self.stoplossmanager.on_next()
        self.takeprofitmanager.on_next()

    def handle_order_completed_trade_managers(self, order):
        sl_result = self.stoplossmanager.handle_order_completed(order)
        tp_result = self.takeprofitmanager.handle_order_completed(order)
        # OCO functionality
        if sl_result and not tp_result:
            self.takeprofitmanager.deactivate(True)
        if not sl_result and tp_result:
            self.stoplossmanager.deactivate(True)

        return sl_result or tp_result

    def on_close_position_trade_managers(self):
        self.stoplossmanager.deactivate(True)
        self.takeprofitmanager.deactivate(True)

    def is_allow_signals_execution(self):
        return not self.stoplossmanager.is_activated() and not self.takeprofitmanager.is_activated()

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