import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S008_AlexNoroSuperTrendStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S008 Alex (Noro) SuperTrend v1.0 Strategy.
    '''

    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("cloud", 25),
        ("Factor", 3),
        ("ATR", 7),
        ("sl", None),
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

        # Super Trend ATR 1
        self.hl2 = 0
        self.Atr1 = btind.AverageTrueRange(self.data, period=self.p.ATR)
        self.Up = 0
        self.Dn = 0
        self.TUp = [0] * 3
        self.TDown = [0] * 3
        self.Trend = [0] * 3

    def calculate_signals(self):
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
                self.Trend.append(self._nzd(self.Trend, -1, 1))

        # Signals
        self.is_open_long = True if self.Trend[-1] == 1 and self.data.close[0] < self.data.open[0] else False
        self.is_close_long = True if self.Trend[-1] == -1 and self.data.close[0] > self.data.open[0] else False
        self.is_open_short = True if self.Trend[-1] == -1 and self.data.close[0] > self.data.open[0] else False
        self.is_close_short = True if self.Trend[-1] == 1 and self.data.close[0] < self.data.open[0] else False

    def print_strategy_debug_info(self):
        self.log('self.hl2 = {}'.format(self.hl2))
        self.log('self.Atr1[0] = {}'.format(self.Atr1[0]))
        self.log('self.Up = {}'.format(self.Up))
        self.log('self.Dn = {}'.format(self.Dn))
        self.log('self.TUp[-1] = {}'.format(self.TUp[-1]))
        self.log('self.TDown[-1] = {}'.format(self.TDown[-1]))
        self.log('self.Trend[-1] = {}'.format(self.Trend[-1]))
