import backtrader.indicators as btind
from datetime import datetime
from strategies.genericstrategy import GenericStrategy


class S007_AlexNoroMultimaStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S007 Alex (Noro) Multima v1.0 strategy.
    '''

    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("usema1", True),
        ("usema2", True),
        ("lenma1", 40),
        ("lenma2", 40),
        ("usecf", True),
        ("sl", None),
        ("tslflag", None),
        ("tp", None),
        ("ttpdist", None),
        ("tbdist", None),
        ("numdca", None),
        ("dcainterval", None),
        ("dcasltimeout", None),
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

    def calculate_signals(self):
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
        up = True if self.lots > 0 and (self.data.close[0] < self.data.open[0] or self.p.usecf is False) else False
        down = True if self.lots < 0 and (self.data.close[0] > self.data.open[0] or self.p.usecf is False) else False
        sig_exit = True if self.lots == 0 else False

        self.is_open_long = True if up is True else False
        self.is_close_long = True if self.position.size > 0 and (down is True or sig_exit is True) else False
        self.is_open_short = True if down is True else False
        self.is_close_short = True if self.position.size < 0 and (up is True or sig_exit is True) else False

    def print_strategy_debug_info(self):
        self.log('self.ma1[0] = {}'.format(self.ma1[0]))
        self.log('self.ma2[0] = {}'.format(self.ma2[0]))
        self.log('self.signal1 = {}'.format(self.signal1))
        self.log('self.signal2 = {}'.format(self.signal2))
        self.log('self.lots = {}'.format(self.lots))

