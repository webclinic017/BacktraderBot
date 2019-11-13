import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S010_AlexAroonTrendStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S010 Alex Aroon Trend v1.0 Strategy.
    '''
    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("aroon_length", 200),
        ("cross_r1_start", 20),
        ("cross_r1_end", 80),
        ("cross_r2_start", 90),
        ("cross_r2_end", 100),
        ("sl", None),
        ("tslflag", None),
        ("tp", None),
        ("ttpdist", None),
        ("tbdist", None),
        ("numdca", None),
        ("dcainterval", None),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 1),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.aroon_upper = btind.AroonUp(period=self.p.aroon_length)
        self.aroon_lower = btind.AroonDown(period=self.p.aroon_length)
        self.openLongCondition = False
        self.openShortCondition = False
        self.closeLongCondition = False
        self.closeShortCondition = False

    def isPositionClosed(self):
        return self.position.size == 0

    def isLongPositionOpen(self):
        return self.position.size > 0

    def isShortPositionOpen(self):
        return self.position.size < 0

    def crossover(self, series1, series2):
        return series1[-1] < series2[-1] and series1[0] >= series2[0]

    def inRange(self, value, minV, maxV):
        return value >= minV and value <= maxV

    def calculate_signals(self):
        if self.isPositionClosed() and self.aroon_upper[0] > self.aroon_lower[0] and \
            self.inRange(self.aroon_lower[0], self.p.cross_r1_start,  self.p.cross_r1_end) and \
            self.inRange(self.aroon_upper[0], self.p.cross_r2_start, self.p.cross_r2_end):
            self.openLongCondition = True
        else:
            self.openLongCondition = False

        if self.isPositionClosed() and self.aroon_upper[0] < self.aroon_lower[0] and \
            self.inRange(self.aroon_upper[0], self.p.cross_r1_start,  self.p.cross_r1_end) and \
            self.inRange(self.aroon_lower[0], self.p.cross_r2_start, self.p.cross_r2_end):
            self.openShortCondition = True
        else:
            self.openShortCondition = False

        if self.isLongPositionOpen() and self.crossover(self.aroon_lower, self.aroon_upper):
            self.closeLongCondition = True
        else:
            self.closeLongCondition = False

        if self.isShortPositionOpen() and self.crossover(self.aroon_upper, self.aroon_lower):
            self.closeShortCondition = True
        else:
            self.closeShortCondition = False

        # Signals
        self.is_open_long = True if self.openLongCondition is True else False
        self.is_close_long = True if self.closeLongCondition is True else False
        self.is_open_short = True if self.openShortCondition is True else False
        self.is_close_short = True if self.closeShortCondition is True else False

    def print_strategy_debug_info(self):
        self.log('self.aroon_upper[0] = {}'.format(self.aroon_upper[0]))
        self.log('self.aroon_lower[0] = {}'.format(self.aroon_lower[0]))
        self.log('self.openLongCondition = {}'.format(self.openLongCondition))
        self.log('self.openShortCondition = {}'.format(self.openShortCondition))
        self.log('self.closeLongCondition = {}'.format(self.closeLongCondition))
        self.log('self.closeShortCondition = {}'.format(self.closeShortCondition))
