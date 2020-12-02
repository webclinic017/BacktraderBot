import backtrader as bt
import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S006_AlexNoroSqueezeMomentumStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S006 Alex (Noro) Squeeze Momentum v1.1 strategy.
    '''

    params = (
        ("debug", False),
        ("wfo_cycle_id", None),
        ("wfo_cycle_training_id", None),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("length", 20),
        ("mult", 2.0),
        ("lengthKC", 20),
        ("multKC", 1.5),
        ("usecolor", True),
        ("usebody", True),
        ("sl", None),
        ("exitmode", None),
        ("tslflag", None),
        ("tp", None),
        ("ttpdist", None),
        ("tbdist", None),
        ("numdca", None),
        ("dcainterval", None),
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

    def calculate_signals(self):
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
        self.is_open_long = True if self.trend[-1] == 1 and (self.bar[-1] == -1 or self.p.usecolor is False) and (self.body[0] > self.abody[0] or self.p.usebody is False) else False
        self.is_close_long = True if self.trend[-1] == -1 and (self.bar[-1] == 1 or self.p.usecolor is False) and (self.body[0] > self.abody[0] or self.p.usebody is False) else False
        self.is_open_short = True if self.trend[-1] == -1 and (self.bar[-1] == 1 or self.p.usecolor is False) and (self.body[0] > self.abody[0] or self.p.usebody is False) else False
        self.is_close_short = True if self.trend[-1] == 1 and (self.bar[-1] == -1 or self.p.usecolor is False) and (self.body[0] > self.abody[0] or self.p.usebody is False) else False

    def print_strategy_debug_info(self):
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

