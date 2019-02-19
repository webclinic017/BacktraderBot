import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
from strategies.abstractstrategy import AbstractStrategy


class S005_AlexNoroTripleRSIStrategy(AbstractStrategy):
    '''
    This is an implementation of a strategy from TradingView - S005 Alex (Noro) Triple RSI v1.1 strategy.
    '''

    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("leverage", 1),
        ("accuracy", 3),
        ("isreversive", False),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 12),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.curtradeid = -1

        # RSI - 2
        self.fastrsi = btind.RSI(self.data.close, period=2, safediv=True)
        # RSI - 7
        self.middlersi = btind.RSI(self.data.close, period=7, safediv=True)
        # RSI - 14
        self.slowrsi = btind.RSI(self.data.close, period=14, safediv=True)

        # Body Filter
        self.body = abs(self.data.close - self.data.open)
        self.abody = btind.SimpleMovingAverage(self.body, period=10)

        # Signals
        self.acc = 0
        self.signalup1 = 0
        self.signalup2 = 0
        self.signalup3 = 0

        self.signaldn1 = 0
        self.signaldn2 = 0
        self.signaldn3 = 0

        self.up = 0
        self.dn = 0
        self.exit = 0

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def next(self):
        # print("next(): id(self)={}".format(id(self)))

        # Signals
        self.acc = 10 - self.p.accuracy
        self.signalup1 = 1 if self.fastrsi[0] < (5 + self.acc) else 0
        self.signalup2 = 1 if self.middlersi[0] < (10 + self.acc * 2) else 0
        self.signalup3 = 1 if self.slowrsi[0] < (15 + self.acc * 3) else 0

        self.signaldn1 = 1 if self.fastrsi[0] > (95 - self.acc) else 0
        self.signaldn2 = 1 if self.middlersi[0] > (90 - self.acc * 2) else 0
        self.signaldn3 = 1 if self.slowrsi[0] > (85 - self.acc * 3) else 0

        self.up = True if self.signalup1 + self.signalup2 + self.signalup3 >= 3 else False
        self.dn = True if self.signaldn1 + self.signaldn2 + self.signaldn3 >= 3 else False
        if self.p.isreversive is False:
            self.exit = True if (self.curr_position > 0 and self.data.close[0] > self.data.open[0] or self.curr_position < 0 and self.data.close[0] < self.data.open[0]) and self.body[0] > self.abody[0] / 3 else False
        else:
            self.exit = False

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
            if self.curr_position < 0 and (self.up or self.p.isreversive is False and self.exit):
                self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.up and self.p.needlong and self.curr_position == 0:
                self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.buy(tradeid=self.curtradeid)
                self.curr_position = 1
                self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position > 0 and (self.dn or self.p.isreversive is False and self.exit):
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.dn and self.p.needshort and self.curr_position == 0:
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
        self.log('self.curtradeid = {}'.format(self.curtradeid))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.fastrsi = {}'.format(self.fastrsi[0]))
        self.log('self.middlersi = {}'.format(self.middlersi[0]))
        self.log('self.slowrsi = {}'.format(self.slowrsi[0]))
        self.log('self.body = {}'.format(self.body[0]))
        self.log('self.abody = {}'.format(self.abody[0]))
        self.log('self.acc = {}'.format(self.acc))
        self.log('self.signalup1 = {}'.format(self.signalup1))
        self.log('self.signalup2 = {}'.format(self.signalup2))
        self.log('self.signalup3 = {}'.format(self.signalup3))
        self.log('self.signaldn1 = {}'.format(self.signaldn1))
        self.log('self.signaldn2 = {}'.format(self.signaldn2))
        self.log('self.signaldn3 = {}'.format(self.signaldn3))
        self.log('self.up = {}'.format(self.up))
        self.log('self.dn = {}'.format(self.dn))
        self.log('self.exit = {}'.format(self.exit))
        self.log('-------------------------------------------------------------------')
