import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
from strategies.abstractstrategy import AbstractStrategy


class S007_AlexNoroMultimaStrategy(AbstractStrategy):
    '''
    This is an implementation of a strategy from TradingView - S007 Alex (Noro) Multima v1.0 strategy.
    '''

    params = (
        ("debug", False),
        ("needlong", True),
        ("needshort", True),
        ("usema1", True),
        ("usema2", True),
        ("lenma1", 40),
        ("lenma2", 40),
        ("usecf", True),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 11),
        ("tomonth", 11),
        ("fromday", 1),
        ("today", 30),
    )

    def __init__(self):
        super().__init__()

        # Strategy
        self.ma1 = btind.SimpleMovingAverage(self.data.close, period=self.p.lenma1)
        self.ma2 = btind.ExponentialMovingAverage(self.data.close, period=self.p.lenma2)
        self.signal1 = 0
        self.signal2 = 0
        self.lots = 0
        self.is_up = 0
        self.is_down = 0
        self.exit = 0

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def next(self):
        # print("next(): id(self)={}".format(id(self)))
        # print("next() - Quick!")

        if self.p.usema1 is False:
            self.signal1 = 0
        else:
            if self.data.close[0] > self.ma1[0]:
                self.signal1 = 1
            else:
                self.signal1 = -1

        if self.p.usema2 is False:
            self.signal2 = 0
        else:
            if self.data.close[0] > self.ma2[0]:
                self.signal2 = 1
            else:
                self.signal2 = -1

        self.lots = self.signal1 + self.signal2

        # Signals
        self.is_up = True if self.lots > 0 and (self.data.close[0] < self.data.open[0] or self.p.usecf is False) else False
        self.is_down = True if self.lots < 0 and (self.data.close[0] > self.data.open[0] or self.p.usecf is False) else False
        self.exit = True if self.lots == 0 else False

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
            if self.curr_position < 0 and (self.is_up is True or self.exit is True):
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

            if self.curr_position > 0 and (self.is_down is True or self.exit is True):
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
        self.log('self.ma1[0] = {}'.format(self.ma1[0]))
        self.log('self.ma2[0] = {}'.format(self.ma2[0]))
        self.log('self.signal1 = {}'.format(self.signal1))
        self.log('self.signal2 = {}'.format(self.signal2))
        self.log('self.lots = {}'.format(self.lots))
        self.log('self.is_up = {}'.format(self.is_up))
        self.log('self.is_down = {}'.format(self.is_down))
        self.log('self.exit = {}'.format(self.exit))
        self.log('----------------------')
