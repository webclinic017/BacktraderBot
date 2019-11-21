from abc import abstractmethod


class BaseStrategyProcessor(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.debug = debug

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
    def get_order_size(self, data, is_long):
        pass

    @abstractmethod
    def open_long_position(self, size):
        pass

    @abstractmethod
    def open_short_position(self, size):
        pass

    @abstractmethod
    def close_position(self):
        pass