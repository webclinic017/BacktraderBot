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

    def printdebuginfo(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        if not self.islivedata():
            ddanalyzer = self.analyzers.dd.get_analysis()
            self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
            self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
            self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
            self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.curtradeid = {}'.format(self.curtradeid))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.position_avg_price = {}'.format(self.position_avg_price))
        self.log('self.data.datetime[0] = {}'.format(self.data.datetime.datetime()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))
        self.log('self.aroon_upper[0] = {}'.format(self.aroon_upper[0]))
        self.log('self.aroon_lower[0] = {}'.format(self.aroon_lower[0]))
        self.log('self.openLongCondition = {}'.format(self.openLongCondition))
        self.log('self.openShortCondition = {}'.format(self.openShortCondition))
        self.log('self.closeLongCondition = {}'.format(self.closeLongCondition))
        self.log('self.closeShortCondition = {}'.format(self.closeShortCondition))
        self.log('self.is_open_long = {}'.format(self.is_open_long))
        self.log('self.is_close_long = {}'.format(self.is_close_long))
        self.log('self.is_open_short = {}'.format(self.is_open_short))
        self.log('self.is_close_short = {}'.format(self.is_close_short))
        self.log('sltpmanager.oco_context = {}'.format(self.strategyprocessor.sltpmanager.oco_context))
        self.log('sltpmanager.sl_order.ref = {}'.format(self.strategyprocessor.sltpmanager.sl_order.ref if self.strategyprocessor.sltpmanager.sl_order else None))
        self.log('sltpmanager.tp_order.ref = {}'.format(self.strategyprocessor.sltpmanager.tp_order.ref if self.strategyprocessor.sltpmanager.tp_order else None))
        self.log('----------------------')
