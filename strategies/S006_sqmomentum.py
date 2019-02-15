import backtrader as bt
import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
from strategies.abstractstrategy import AbstractStrategy


class S006_AlexNoroSqueezeMomentumStrategy(AbstractStrategy):
    '''
    This is an implementation of a strategy from TradingView - S006 Alex (Noro) Squeeze Momentum v1.1 strategy.
    '''

    params = (
        ("debug", False),
        ("needlong", True),
        ("needshort", True),
        ("length", 20),
        ("mult", 2.0),
        ("lengthKC", 20),
        ("multKC", 1.5),
        ("usecolor", True),
        ("usebody", True),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 11),
        ("tomonth", 11),
        ("fromday", 1),
        ("today", 30),
    )

    def __init__(self):
        super().__init__()

        # Calculate BB
        self.basis = btind.SimpleMovingAverage(self.data.close, period=self.p.length)
        self.dev = self.p.multKC * btind.StdDev(self.data.close,  period=self.p.length)
        self.upperBB = 0
        self.lowerBB = 0

        # Calculate KC
        self.ma = btind.SimpleMovingAverage(self.data.close, period=self.p.lengthKC)
        self.range = btind.TrueRange(self.data)
        self.rangema = btind.SimpleMovingAverage(self.range, period=self.p.lengthKC)
        self.upperKC = 0
        self.lowerKC = 0

        self.sqzOn = 0
        self.sqzOff = 0
        self.noSqz = 0

        self.highest1 = bt.talib.MAX(self.data.high, timeperiod=self.p.lengthKC)
        self.lowest1 = bt.talib.MIN(self.data.low, timeperiod=self.p.lengthKC)
        self.sma1 = bt.talib.SMA(self.data.close, timeperiod=self.p.lengthKC)
        self.avg1 = (self.highest1 + self.lowest1) / 2
        self.avg2 = (self.avg1 + self.sma1) / 2
        self.lrsrc = self.data.close - self.avg2
        self.val = bt.talib.LINEARREG(self.lrsrc, timeperiod=self.p.lengthKC)
        self.trend = [0]

        # Body Filter
        self.body = abs(self.data.close - self.data.open)
        self.abody = btind.SimpleMovingAverage(self.body, period=10) / 3

        # BarColor
        self.bar = [0]

        self.is_up = 0
        self.is_down = 0

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def next(self):
        # print("next(): id(self)={}".format(id(self)))
        # print("next() - Quick!")

        # Calculate BB
        self.upperBB = self.basis[0] + self.dev[0]
        self.lowerBB = self.basis[0] - self.dev[0]

        # Calculate KC
        self.upperKC = self.ma[0] + self.rangema[0] * self.p.multKC
        self.lowerKC = self.ma[0] - self.rangema[0] * self.p.multKC

        self.sqzOn = True if self.lowerBB > self.lowerKC and self.upperBB < self.upperKC else False
        self.sqzOff = True if (self.lowerBB < self.lowerKC) and (self.upperBB > self.upperKC) else False
        self.noSqz = True if (self.sqzOn is False) and (self.sqzOff is False) else False

        # Trend
        if self.val[0] > 0:
            self.trend.append(1)
        else:
            if self.val[0] < 0:
                self.trend.append(-1)
            else:
                self.trend.append(0)

        # BarColor
        if self.data.close[0] > self.data.open[0]:
            self.bar.append(1)
        else:
            if self.data.close[0] < self.data.open[0]:
                self.bar.append(-1)
            else:
                self.bar.append(0)

        # Signals
        self.is_up = True if self.trend[-1] == 1 and (self.bar[-1] == -1 or self.p.usecolor is False) and (self.body[0] > self.abody[0] or self.p.usebody is False) else False
        self.is_down = True if self.trend[-1] == -1 and (self.bar[-1] == 1 or self.p.usecolor is False) and (self.body[0] > self.abody[0] or self.p.usebody is False) else False

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

            if self.curr_position > 0 and self.is_down is True:
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.is_down is True and self.p.needshort is True:
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
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.data.open[0] = {}'.format(self.data.open[0]))
        self.log('self.data.high[0] = {}'.format(self.data.high[0]))
        self.log('self.data.low[0] = {}'.format(self.data.low[0]))
        self.log('self.data.close[0] = {}'.format(self.data.close[0]))
        self.log('self.basis[0] = {}'.format(self.basis[0]))
        self.log('self.dev[0] = {}'.format(self.dev[0]))
        self.log('self.upperBB = {}'.format(self.upperBB))
        self.log('self.lowerBB = {}'.format(self.lowerBB))
        self.log('self.ma[0] = {}'.format(self.ma[0]))
        self.log('self.range[0] = {}'.format(self.range[0]))
        self.log('self.rangema[0] = {}'.format(self.rangema[0]))
        self.log('self.upperKC = {}'.format(self.upperKC))
        self.log('self.lowerKC = {}'.format(self.lowerKC))
        self.log('self.sqzOn = {}'.format(self.sqzOn))
        self.log('self.sqzOff = {}'.format(self.sqzOff))
        self.log('self.noSqz = {}'.format(self.noSqz))
        self.log('self.highest1[0] = {}'.format(self.highest1[0]))
        self.log('self.lowest1[0] = {}'.format(self.lowest1[0]))
        self.log('self.sma1[0] = {}'.format(self.sma1[0]))
        self.log('self.avg1[0] = {}'.format(self.avg1[0]))
        self.log('self.avg2[0] = {}'.format(self.avg2[0]))
        self.log('self.lrsrc[0] = {}'.format(self.lrsrc[0]))
        self.log('self.val[0] = {}'.format(self.val[0]))
        self.log('self.trend[-1] = {}'.format(self.trend[-1]))
        self.log('self.body[0] = {}'.format(self.body[0]))
        self.log('self.abody[0] = {}'.format(self.abody[0]))
        self.log('self.bar[-1] = {}'.format(self.bar[-1]))
        self.log('self.is_up = {}'.format(self.is_up))
        self.log('self.is_down = {}'.format(self.is_down))
        self.log('----------------------')
