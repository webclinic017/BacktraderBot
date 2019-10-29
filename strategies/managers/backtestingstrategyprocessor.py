from .strategyprocessor import BaseStrategyProcessor
import backtrader as bt


class BacktestingStrategyProcessor(BaseStrategyProcessor):

    def __init__(self, strategy, debug):
        super().__init__(strategy, debug)
        self.strategy = strategy
        self.broker = strategy.broker
        self.analyzers = strategy.analyzers
        self.data = strategy.data
        self.debug = debug

    def set_startcash(self, startcash):
        self.broker.setcash(startcash)
        # TODO: Workaround
        self.analyzers.dd.p.initial_cash = startcash
        self.analyzers.dd.maxportfoliovalue = startcash

        self.analyzers.ta.p.cash = startcash

    def log(self, txt, send_telegram_flag=False):
        if self.debug:
            dt = self.strategy.data.datetime.datetime()
            print('%s  %s' % (dt, txt))

    def notify_data(self, data, status, *args, **kwargs):
        pass

    def notify_analyzers(self):
        ddanalyzer = self.strategy.analyzers.dd
        ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately

    def open_long_position(self):
        order = self.strategy.generic_buy(tradeid=self.strategy.curtradeid, exectype=bt.Order.Market)
        self.log("BUY MARKET base order submitted: order.ref={}, order.size={}, curtradeid={}".format(order.ref, order.size, self.strategy.curtradeid))
        return order

    def open_short_position(self):
        order = self.strategy.generic_sell(tradeid=self.strategy.curtradeid, exectype=bt.Order.Market)
        self.log("SELL MARKET base order submitted: order.ref={}, order.size={}, curtradeid={}".format(order.ref, order.size, self.strategy.curtradeid))
        return order

    def close_position(self):
        order = self.strategy.generic_close(tradeid=self.strategy.curtradeid)
        self.log("Closed position by MARKET order: order.ref={}, curtradeid={}".format(order.ref, self.strategy.curtradeid))
        return order
