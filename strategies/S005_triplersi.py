import backtrader.indicators as btind
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
        ("indi", 3),
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

    def calculate_signals(self):
        # Signals
        self.acc = 10 - self.p.accuracy
        self.signalup1 = 1 if self.fastrsi[0] < (5 + self.acc) else 0
        self.signalup2 = 1 if self.middlersi[0] < (10 + self.acc * 2) else 0
        self.signalup3 = 1 if self.slowrsi[0] < (15 + self.acc * 3) else 0

        self.signaldn1 = 1 if self.fastrsi[0] > (95 - self.acc) else 0
        self.signaldn2 = 1 if self.middlersi[0] > (90 - self.acc * 2) else 0
        self.signaldn3 = 1 if self.slowrsi[0] > (85 - self.acc * 3) else 0

        self.is_open_long = True if self.signalup1 + self.signalup2 + self.signalup3 >= self.p.indi else False
        self.is_open_short = True if self.signaldn1 + self.signaldn2 + self.signaldn3 >= self.p.indi else False
        if self.p.isreversive is True:
            self.is_close_long = True if self.signaldn1 + self.signaldn2 + self.signaldn3 >= self.p.indi else False
            self.is_close_short = True if self.signalup1 + self.signalup2 + self.signalup3 >= self.p.indi else False
        else:
            self.is_close_long = True if self.position.size > 0 and self.data.close[0] > self.data.open[0] and self.body[0] > self.abody[0] / 3 else False
            self.is_close_short = True if self.position.size < 0 and self.data.close[0] < self.data.open[0] and self.body[0] > self.abody[0] / 3 else False

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
        self.log('self.is_open_long = {}'.format(self.is_open_long))
        self.log('self.is_close_long = {}'.format(self.is_close_long))
        self.log('self.is_open_short = {}'.format(self.is_open_short))
        self.log('self.is_close_short = {}'.format(self.is_close_short))
        self.log('-------------------------------------------------------------------')
