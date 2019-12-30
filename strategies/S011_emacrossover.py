import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S011_EMACrossOverStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S011 EMA CrossOver v1.0 Strategy.
    '''
    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("ema_ratio", 0.5),
        ("slow_ema_period", 200),
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

        self.fast_ema_period = round(self.p.ema_ratio * self.p.slow_ema_period)
        self.fastEMA = btind.ExponentialMovingAverage(self.data.close, period=self.fast_ema_period)
        self.slowEMA = btind.ExponentialMovingAverage(self.data.close, period=self.p.slow_ema_period)
        self.openLongPositionCriteria = False
        self.openShortPositionCriteria = False
        self.signalOpenPosition = None

    def crossover(self, series1, series2):
        return series1[-1] < series2[-1] and series1[0] >= series2[0]

    def calculate_signals(self):
        # Calculate signal to determine whether eligible to open a new position
        self.openLongPositionCriteria = self.crossover(self.fastEMA, self.slowEMA)
        self.openShortPositionCriteria = self.crossover(self.slowEMA, self.fastEMA)

        if self.openLongPositionCriteria is True:
            self.signalOpenPosition = 1
        else:
            if self.openShortPositionCriteria is True:
                self.signalOpenPosition = -1
            else:
                self.signalOpenPosition = None

        # Signals
        self.is_open_long = True if self.signalOpenPosition == 1 else False
        self.is_close_long = True if self.signalOpenPosition == -1 else False
        self.is_open_short = True if self.signalOpenPosition == -1 else False
        self.is_close_short = True if self.signalOpenPosition == 1 else False

    def print_strategy_debug_info(self):
        self.log('self.fast_ema_period = {}'.format(self.fast_ema_period))
        self.log('self.fastEMA[0] = {}'.format(self.fastEMA[0]))
        self.log('self.slowEMA[0] = {}'.format(self.slowEMA[0]))
        self.log('self.openLongPositionCriteria = {}'.format(self.openLongPositionCriteria))
        self.log('self.openShortPositionCriteria = {}'.format(self.openShortPositionCriteria))
        self.log('self.signalOpenPosition = {}'.format(self.signalOpenPosition))
