import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
from strategies.abstractstrategy import AbstractStrategy


class S011_EMACrossOverStrategy(AbstractStrategy):
    '''
    This is an implementation of a strategy from TradingView - S011 EMA CrossOver v1.0 Strategy.
    '''
    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("ema_ratio", 0.5),
        ("slow_ema_period", 200),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 1),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.fast_ema_period = round(self.p.ema_ratio * self.p.slow_ema_period)
        self.fastEMA = btind.ExponentialMovingAverage(self.data.close, period=self.fast_ema_period)
        self.slowEMA = btind.ExponentialMovingAverage(self.data.close, period=self.p.slow_ema_period)
        self.openLongPositionCriteria = False
        self.openShortPositionCriteria = False
        self.signalOpenPosition = None
        self.is_up = False
        self.is_dn = False
        self.exit = False

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def crossover(self, series1, series2):
        return series1[-1] < series2[-1] and series1[0] >= series2[0]

    def next(self):
        # print("next(): id(self)={}".format(id(self)))
        # print("next() - Quick!")

        # Calculate signal to determine whether eligible to open a new position
        self.openLongPositionCriteria = self.crossover(self.fastEMA, self.slowEMA)
        self.openShortPositionCriteria = self.crossover(self.slowEMA, self.fastEMA)

        if self.openLongPositionCriteria is True:
            self.signalOpenPosition = 1
        else:
            if self.openShortPositionCriteria is True:
                self.signalOpenPosition = -1
            else:
                self.signalOpenPosition = None

        # Signals
        self.is_up = True if self.signalOpenPosition == 1 else False
        self.is_dn = True if self.signalOpenPosition == -1 else False

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
            if self.curr_position < 0 and self.is_up is True:
                self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.is_up is True and self.p.needlong is True:
                self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.buy(tradeid=self.curtradeid)
                self.curr_position = 1
                self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position > 0 and self.is_dn is True:
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.is_dn is True and self.p.needshort is True:
                self.log('!!! BEFORE OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.sell(tradeid=self.curtradeid)
                self.curr_position = -1
                self.log('!!! AFTER OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

        if self.currdt > self.todt:
            self.log('!!! Time passed beyond date range')
            if self.curr_position != 0:  # if 'curtradeid' in self:
                self.log('!!! Closing trade prematurely')
                self.close(tradeid=self.curtradeid)
            self.curr_position = 0

    def printdebuginfonextinner(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        ddanalyzer = self.analyzers.dd.get_analysis()
        self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
        self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.position_avg_price = {}'.format(self.position_avg_price))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))
        self.log('self.fast_ema_period = {}'.format(self.fast_ema_period))
        self.log('self.fastEMA[0] = {}'.format(self.fastEMA[0]))
        self.log('self.slowEMA[0] = {}'.format(self.slowEMA[0]))
        self.log('self.openLongPositionCriteria = {}'.format(self.openLongPositionCriteria))
        self.log('self.openShortPositionCriteria = {}'.format(self.openShortPositionCriteria))
        self.log('self.signalOpenPosition = {}'.format(self.signalOpenPosition))
        self.log('self.is_up = {}'.format(self.is_up))
        self.log('self.is_dn = {}'.format(self.is_dn))
        self.log('----------------------')
