import backtrader as bt
from abc import abstractmethod
import itertools
from datetime import datetime
import pytz
from strategies.livetradingstrategyprocessor import LiveTradingStrategyProcessor
from strategies.backtestingstrategyprocessor import BacktestingStrategyProcessor
from termcolor import colored


class StrategyProcessorFactory(object):
    @classmethod
    def build_strategy_processor(cls, strategy, debug):
        if strategy.data.islive():
            return LiveTradingStrategyProcessor(strategy, debug)
        else:
            return BacktestingStrategyProcessor(strategy, debug)


class GenericStrategy(bt.Strategy):

    def __init__(self):
        self.curtradeid = -1
        self.curr_position = 0
        self.position_avg_price = 0
        self.tradesopen = {}
        self.tradesclosed = {}

        self.is_open_long = False
        self.is_close_long = False
        self.is_open_short = False
        self.is_close_short = False

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        self.strategyprocessor = StrategyProcessorFactory.build_strategy_processor(self, self.p.debug)

    def islive(self):
        return self.data.islive()

    def log(self, txt, dt=None):
        if self.p.debug:
            dt = dt or self.data.datetime.datetime()
            print('%s  %s' % (dt, txt))

    def check_arr_equal(self, arr, val, last_num):
        cmp_arr = arr[len(arr) - last_num:len(arr)]
        return cmp_arr[0] == val and cmp_arr[1:] == cmp_arr[:-1]

    def _nz(self, data_arr, idx):
        if len(data_arr) < (abs(idx) + 1):
            return 0
        else:
            return data_arr[idx]

    def _nzd(self, data_arr, idx, defvalue):
        if len(data_arr) < (abs(idx) + 1):
            return defvalue
        else:
            return data_arr[idx]

    def notify_data(self, data, status, *args, **kwargs):
        return self.strategyprocessor.notify_data(data, status, args, kwargs)

    def start(self):
        self.strategyprocessor.set_startcash(self.p.startcash)

    @abstractmethod
    def calculate_signals(self):
        pass

    @abstractmethod
    def printdebuginfonextinner(self):
        pass

    def next(self):
        if self.islive():
            print("next(): id(self)={}".format(id(self)))

        self.calculate_signals()

        # Trading
        self.fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        self.todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59, 59)
        self.currdt = self.data.datetime.datetime()

        self.gmt3_tz = pytz.timezone('Etc/GMT-3')
        self.fromdt = pytz.utc.localize(self.fromdt)
        self.todt = pytz.utc.localize(self.todt)
        self.currdt = self.gmt3_tz.localize(self.currdt, is_dst=True)

        self.printdebuginfonextinner()

        if self.currdt > self.fromdt and self.currdt < self.todt:
            if self.curr_position < 0 and self.is_close_short is True:
                self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.strategyprocessor.close()
                self.curr_position = 0
                self.position_avg_price = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.p.needlong is True and self.is_open_long is True:
                self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.strategyprocessor.buy()
                self.curr_position = 1
                self.position_avg_price = self.data.close[0]
                self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position > 0 and self.is_close_long is True:
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.strategyprocessor.close()
                self.curr_position = 0
                self.position_avg_price = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.p.needshort is True and self.is_open_short is True:
                self.log('!!! BEFORE OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.strategyprocessor.sell()
                self.curr_position = -1
                self.position_avg_price = self.data.close[0]
                self.log('!!! AFTER OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

        if self.currdt > self.todt:
            self.log('!!! Time passed beyond date range')
            if self.curr_position != 0:  # if 'curtradeid' in self:
                self.log('!!! Closing trade prematurely')
                self.strategyprocessor.close()
            self.curr_position = 0
            self.position_avg_price = 0

    def notify_order(self, order):
        self.log('notify_order() - Order Ref={}, Status={}, order.size={}, Broker Cash={}, self.position.size = {}'.format(order.ref, order.Status[order.status], order.size, self.broker.getcash(), self.position.size))
        if order.status in [bt.Order.Created, bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = 'BUY COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price, bt.num2date(order.executed.dt))
                self.log(buytxt)
            else:
                selltxt = 'SELL COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price, bt.num2date(order.executed.dt))
                self.log(selltxt)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected: Status {}'.format(order.Status[order.status]))
            self.curr_position = 0
            if order.status == order.Margin:
                self.log('notify_order() - ********** MARGIN CALL!! SKIP ORDER AND PREPARING FOR NEXT ORDERS!! **********')

    def get_trade_log_profit_color(self, trade):
        return 'red' if trade.pnl < 0 else 'green'

    def notify_trade(self, trade):
        self.log('!!! BEGIN notify_trade() - id(self)={}, self.curr_position={}, traderef={}, self.broker.getcash()={}'.format(id(self), self.curr_position, trade.ref, self.broker.getcash()))

        if trade.justopened:
            self.tradesopen[trade.ref] = trade
            self.log('TRADE JUST OPENED, SIZE={}, REF={}, VALUE={}, COMMISSION={}, BROKER CASH={}'.format(trade.size, trade.ref, trade.value, trade.commission, self.broker.getcash()))

        if trade.isclosed:
            self.tradesclosed[trade.ref] = trade
            self.log('---------------------------- TRADE CLOSED --------------------------')
            self.log("1: Data Name:                            {}".format(trade.data._name))
            self.log("2: Bar Num:                              {}".format(len(trade.data)))
            self.log("3: Current date:                         {}".format(self.data.datetime.date()))
            self.log('4: Status:                               Trade Complete')
            self.log('5: Ref:                                  {}'.format(trade.ref))
            self.log('6: PnL:                                  {}'.format(round(trade.pnl, 2)))
            self.log(colored('OPERATION PROFIT, GROSS {:.8f}, NET {:.8f}'.format(trade.pnl, trade.pnlcomm), self.get_trade_log_profit_color(trade)))
            self.log('--------------------------------------------------------------------')

