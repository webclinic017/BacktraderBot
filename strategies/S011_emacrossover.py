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
        self.log('self.fast_ema_period = {}'.format(self.fast_ema_period))
        self.log('self.fastEMA[0] = {}'.format(self.fastEMA[0]))
        self.log('self.slowEMA[0] = {}'.format(self.slowEMA[0]))
        self.log('self.openLongPositionCriteria = {}'.format(self.openLongPositionCriteria))
        self.log('self.openShortPositionCriteria = {}'.format(self.openShortPositionCriteria))
        self.log('self.signalOpenPosition = {}'.format(self.signalOpenPosition))
        self.log('self.is_open_long = {}'.format(self.is_open_long))
        self.log('self.is_close_long = {}'.format(self.is_close_long))
        self.log('self.is_open_short = {}'.format(self.is_open_short))
        self.log('self.is_close_short = {}'.format(self.is_close_short))
        self.log('sltpmanager.oco_context = {}'.format(self.strategyprocessor.sltpmanager.oco_context))
        self.log('sltpmanager.sl_order.ref = {}'.format(self.strategyprocessor.sltpmanager.sl_order.ref if self.strategyprocessor.sltpmanager.sl_order else None))
        self.log('sltpmanager.tp_order.ref = {}'.format(self.strategyprocessor.sltpmanager.tp_order.ref if self.strategyprocessor.sltpmanager.tp_order else None))
        self.log('----------------------')
