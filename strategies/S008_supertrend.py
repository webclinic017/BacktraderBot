import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
from strategies.abstractstrategy import AbstractStrategy

class S008_AlexNoroSuperTrendStrategy(AbstractStrategy):
    '''
    This is an implementation of a strategy from TradingView - S008 Alex (Noro) SuperTrend v1.0 Strategy.
    '''

    params = (
        ("debug", False),
        ("needlong", True),
        ("needshort", True),
        ("cloud", 25),
        ("Factor", 3),
        ("ATR", 7),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 11),
        ("tomonth", 11),
        ("fromday", 1),
        ("today", 30),
    )

    def __init__(self):
        super().__init__()

        # Super Trend ATR 1
        self.hl2 = 0
        self.Atr1 = btind.AverageTrueRange(self.data, period=self.p.ATR)
        self.Up = 0
        self.Dn = 0
        self.TUp = [0] * 3
        self.TDown = [0] * 3
        self.Trend = [0] * 3
        self.is_up = 0
        self.is_down = 0

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def start(self):
        # Check whether to skip this testing round
        # print("start(): id(self)={}".format(id(self)))
        if self.p.needlong is False and self.p.needshort is False:
            self.env.runstop()

    def next(self):
        # print("next(): id(self)={}".format(id(self)))
        # print("next() - Quick!")

        # Super Trend ATR 1
        self.hl2 = (self.data.high[0] + self.data.low[0]) / 2
        self.Up = self.hl2 - (self.p.Factor * self.Atr1[0])
        self.Dn = self.hl2 + (self.p.Factor * self.Atr1[0])
        if self.data.close[-1] > self.TUp[-1]:
            self.TUp.append(max(self.Up, self.TUp[-1]))
        else:
            self.TUp.append(self.Up)
        if self.data.close[-1] < self.TDown[-1]:
            self.TDown.append(min(self.Dn, self.TDown[-1]))
        else:
            self.TDown.append(self.Dn)

        # Trend
        if self.data.close[0] > self.TDown[-2]:
            self.Trend.append(1)
        else:
            if self.data.close[0] < self.TUp[-2]:
                self.Trend.append(-1)
            else:
                self.Trend.append(self._nz(self.Trend, -1, 1))

        # Signals
        self.is_up = True if self.Trend[-1] == 1 and self.data.close[0] < self.data.open[0] else False
        self.is_down = True if self.Trend[-1] == -1 and self.data.close[0] > self.data.open[0] else False

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
        self.log('self.position_avg_price = {}'.format(self.position_avg_price))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))
        self.log('self.hl2 = {}'.format(self.hl2))
        self.log('self.Atr1[0] = {}'.format(self.Atr1[0]))
        self.log('self.Up = {}'.format(self.Up))
        self.log('self.Dn = {}'.format(self.Dn))
        self.log('self.TUp[-1] = {}'.format(self.TUp[-1]))
        self.log('self.TDown[-1] = {}'.format(self.TDown[-1]))
        self.log('self.Trend[-1] = {}'.format(self.Trend[-1]))
        self.log('self.is_up = {}'.format(self.is_up))
        self.log('self.is_down = {}'.format(self.is_down))
        self.log('----------------------')
