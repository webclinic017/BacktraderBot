from abc import abstractmethod
from strategies.managers.sltpmanager import SLTPManager
from strategies.managers.trailingbuymanager import TrailingBuyManager
from strategies.managers.dcamodemanager import DcaModeManager


class OcoContext(object):
    def __init__(self):
        self.sl_order = None
        self.tp_order = None

    def reset(self):
        self.sl_order = None
        self.tp_order = None

    def get_sl_order(self):
        return self.sl_order

    def set_sl_order(self, order):
        self.sl_order = order

    def get_tp_order(self):
        return self.tp_order

    def set_tp_order(self, order):
        self.tp_order = order

    def is_sl_order(self, order):
        if order and self.sl_order and order.ref == self.sl_order.ref:
            return True

    def is_tp_order(self, order):
        if order and self.tp_order and order.ref == self.tp_order.ref:
            return True

    def __str__(self):
        sl_order_ref = self.sl_order.ref if self.sl_order else None
        tp_order_ref = self.tp_order.ref if self.tp_order else None
        return "OcoContext <sl_order.ref={}, tp_order.ref={}>".format(sl_order_ref, tp_order_ref)


class BaseStrategyProcessor(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.debug = debug
        self.oco_context = OcoContext()
        self.sltpmanager = SLTPManager(strategy, self.oco_context)
        self.trailingbuymanager = TrailingBuyManager(strategy)
        self.dcamodemanager = DcaModeManager(strategy, self.oco_context)

    def activate_trade_entry_managers(self, tradeid, last_price, is_long):
        self.trailingbuymanager.activate_tb(tradeid, last_price, is_long)
        self.dcamodemanager.activate_dca_mode(tradeid, last_price, is_long)

    def activate_position_trade_managers(self, tradeid, pos_price, pos_size, is_long):
        self.sltpmanager.activate_sl(tradeid, pos_price, pos_size, is_long)
        self.sltpmanager.activate_tp(tradeid, pos_price, pos_size, is_long)

    def on_next_trade_managers(self):
        self.sltpmanager.move_targets()
        self.trailingbuymanager.move_targets()

        self.sltpmanager.sl_on_next()
        self.sltpmanager.tp_on_next()
        self.trailingbuymanager.tb_on_next()

    def handle_order_completed_trailing_buy(self, order):
        return self.trailingbuymanager.handle_order_completed(order)

    def handle_order_completed_dca_mode(self, order):
        return self.dcamodemanager.handle_order_completed(order)

    def handle_order_completed_trade_managers(self, order):
        return self.sltpmanager.handle_order_completed(order)

    def deactivate_entry_trade_managers(self):
        self.dcamodemanager.dca_mode_deactivate()
        self.trailingbuymanager.tb_deactivate()

    def deactivate_trade_managers(self):
        self.sltpmanager.sl_deactivate()
        self.sltpmanager.tp_deactivate()

    def is_allow_signals_execution(self):
        return not self.sltpmanager.is_tp_mode_activated() and not self.trailingbuymanager.is_tb_mode_activated() and not self.dcamodemanager.is_dca_mode_activated()

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