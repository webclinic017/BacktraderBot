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
        self.strategy_analyzers = strategy.analyzers

    def notify_trade_managers_open_trade(self, trade):
        self.stoplossmanager.open_trade(trade)
        self.takeprofitmanager.open_trade(trade)

    def notify_trade_managers_process_next(self):
        self.stoplossmanager.process_next()
        self.takeprofitmanager.process_next()

    def notify_trade_analyzers(self, trade):
        if self.stoplossmanager.is_sl_triggered_trade_result():
            self.strategy_analyzers.ta.update_stoploss_data(trade.pnlcomm, False)
        if self.stoplossmanager.is_tsl_triggered_trade_result():
            self.strategy_analyzers.ta.update_stoploss_data(trade.pnlcomm, True)
        if self.takeprofitmanager.is_tp_triggered_trade_result():
            self.strategy_analyzers.ta.update_takeprofit_data(trade.pnlcomm, False)
        if self.takeprofitmanager.is_ttp_triggered_trade_result():
            self.strategy_analyzers.ta.update_takeprofit_data(trade.pnlcomm, True)

    def notify_trade_managers_close_trade(self, trade):
        self.stoplossmanager.close_trade(trade)
        self.takeprofitmanager.close_trade(trade)
        self.notify_trade_analyzers(trade)

    def is_allow_signals_execution(self):
        return not self.stoplossmanager.is_activated() and not self.takeprofitmanager.is_activated()

    @abstractmethod
    def log(self, txt, send_telegram_flag=False):
        pass

    @abstractmethod
    def check_order_expired(self, order):
        pass

    @abstractmethod
    def handle_pending_order(self, order):
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
    def buy(self):
        pass

    @abstractmethod
    def sell(self):
        pass

    @abstractmethod
    def close(self):
        pass