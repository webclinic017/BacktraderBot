import backtrader as bt
import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S002_AlexNoroSILAStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S002 Alex (Noro) SILA v1.6.1L strategy.
    '''

    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("sensup", 5),
        ("sensdn", 5),
        ("usewow", True),
        ("usebma", True),
        ("usebc", True),
        ("usest", True),
        ("usedi", True),
        ("usetts", True),
        ("usersi", True),
        ("usewto", True),
        ("uselocoentry", False),
        ("sl", None),
        ("tslflag", None),
        ("tp", None),
        ("ttpdist", None),
        ("tbdist", None),
        ("numdca", None),
        ("dcainterval", None),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 12),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        # WOW 1.0 method
        self.lasthigh = btind.Highest(self.data.close, period=30)
        self.lastlow = btind.Lowest(self.data.close, period=30)
        self.center = [0.0]
        self.trend1 = [0, 0]
        self.trend2 = [0, 0]
        self.WOWtrend = [0, 0]

        # BestMA 1.0 method
        self.SMAOpen = bt.talib.SMA(self.data.open, timeperiod=30) #btind.MovingAverageSimple(self.data.open, period=30)
        self.SMAClose = bt.talib.SMA(self.data.close, timeperiod=30) #btind.MovingAverageSimple(self.data.close, period=30)
        self.BMAtrend = [0, 0]

        # BarColor 1.0 method
        self.color = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.BARtrend = [0, 0]

        # SuperTrend mehtod
        self.Atr3 = btind.AverageTrueRange(self.data, period=3)
        self.TrendUp = [0, 0, 0]
        self.TrendDn = [0, 0, 0]
        self.SUPtrend = [0, 0]

        # DI method
        self.TrueRange = btind.TrueRange(self.data)
        self.DirectionalMovementPlus = [0, 0]
        self.DirectionalMovementMinus = [0, 0]
        self.SmoothedTrueRange = [0.0, 0.0]
        self.SmoothedDirectionalMovementPlus = [0.0, 0.0]
        self.SmoothedDirectionalMovementMinus = [0.0, 0.0]
        self.DIPlus = [0.0, 0.0]
        self.DIMinus = [0.0, 0.0]
        self.DItrend = [0, 0]

        # TTS method(Trend Trader Strategy)
        # Start of HPotter's code
        # Andrew Abraham' idea
        self.Atr1 = btind.AverageTrueRange(self.data, period=1)
        self.avgTR = btind.WeightedMovingAverage(self.Atr1, period=21)
        self.highestC = btind.Highest(self.data.high, period=21)
        self.lowestC = btind.Lowest(self.data.low, period=21)
        self.ret = [0, 0]
        self.pos = [0, 0]
        # End of HPotter 's code
        self.TTStrend = [0, 0]

        # RSI method
        self.RSI13 = btind.RSI(self.data.close, period=13, safediv=True)
        self.RSItrend = [0, 0]

        # WTO("WaveTrend Oscilator") method by LazyBear
        # Start of LazyBear's code
        self.hlc3 = (self.data.high + self.data.low + self.data.close) / 3
        self.esa = btind.ExponentialMovingAverage(self.hlc3, period=10)
        self.hlc3esa = abs(self.hlc3 - self.esa)
        self.d = btind.ExponentialMovingAverage(self.hlc3esa, period=10)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.tci = btind.ExponentialMovingAverage(self.ci, period=21)
        # End of LazyBear's code
        self.WTOtrend = [0, 0]

        self.trends = [0, 0]
        self.posi = [0, 0]
        self.arr = [0, 0]
        self.bar = [0, 0, 0]
        self.locotop = [0, 0]
        self.locobot = [0, 0]
        self.entry = [0, 0]

    def calculate_signals(self):
        # WOW 1.0 method
        self.center.append((self.lasthigh[0] + self.lastlow[0]) / 2)
        self.body = (self.data.open[0] + self.data.close[0]) / 2
        if self.body > self.center[-1]:
            self.trend1.append(1)
        else:
            if self.body < self.center[-1]:
                self.trend1.append(-1)
            else:
                self.trend1.append(self.trend1[-1])
        if self.center[-1] > self.center[-2]:
            self.trend2.append(1)
        else:
            if self.center[-1] < self.center[-2]:
                self.trend2.append(-1)
            else:
                self.trend2.append(self.trend2[-1])

        if self.p.usewow is True:
            if self.trend1[-1] == 1 and self.trend2[-1] == 1:
                self.WOWtrend.append(1)
            else:
                if self.trend1[-1] == -1 and self.trend2[-1] == -1:
                    self.WOWtrend.append(-1)
                else:
                    self.WOWtrend.append(self.WOWtrend[-1])
        else:
            self.WOWtrend.append(0)

        # BestMA 1.0 method
        if self.p.usebma is True:
            if self.SMAClose[0] > self.SMAOpen[0]:
                self.BMAtrend.append(1)
            else:
                if self.SMAClose[0] < self.SMAOpen[0]:
                    self.BMAtrend.append(-1)
                else:
                    self.BMAtrend.append(self.BMAtrend[-1])
        else:
            self.BMAtrend.append(0)

        # BarColor 1.0 method
        if self.data.close[0] > self.data.open[0]:
            self.color.append(1)
        else:
            self.color.append(0)
        self.score = self.color[-1] + self.color[-2] + self.color[-3] + self.color[-4] + self.color[-5] + self.color[-6] + self.color[-7] + self.color[-8]
        if self.p.usebc is True:
            if self.score > 5:
                self.BARtrend.append(1)
            else:
                if self.score < 3:
                    self.BARtrend.append(-1)
                else:
                    self.BARtrend.append(self.BARtrend[-1])
        else:
            self.BARtrend.append(0)

        # SuperTrend mehtod
        self.Up = (self.data.high[0] + self.data.low[0]) / 2 - (7 * self.Atr3[0])
        self.Dn = (self.data.high[0] + self.data.low[0]) / 2 + (7 * self.Atr3[0])
        if self.data.close[-1] > self.TrendUp[-1]:
            self.TrendUp.append(max(self.Up, self.TrendUp[-1]))
        else:
            self.TrendUp.append(self.Up)
        if self.data.close[-1] < self.TrendDn[-1]:
            self.TrendDn.append(min(self.Dn, self.TrendDn[-1]))
        else:
            self.TrendDn.append(self.Dn)
        if self.p.usest is True:
            if self.data.close[0] > self.TrendDn[-2]:
                self.SUPtrend.append(1)
            else:
                if self.data.close[0] < self.TrendUp[-2]:
                    self.SUPtrend.append(-1)
                else:
                    self.SUPtrend.append(self.SUPtrend[-1])
        else:
            self.SUPtrend.append(0)

        # DI method
        if self.data.high[0] - self._nz(self.data.high, -1) > self._nz(self.data.low, -1) - self.data.low[0]:
            self.DirectionalMovementPlus.append(max(self.data.high[0] - self._nz(self.data.high, -1), 0))
        else:
            self.DirectionalMovementPlus.append(0)
        if self._nz(self.data.low, -1) - self.data.low[0] > self.data.high[0] - self._nz(self.data.high, -1):
            self.DirectionalMovementMinus.append(max(self._nz(self.data.low, -1) - self.data.low[0], 0))
        else:
            self.DirectionalMovementMinus.append(0)
        self.SmoothedTrueRange.append(self._nz(self.SmoothedTrueRange, -1) - (self._nz(self.SmoothedTrueRange, -1) / 14) + self.TrueRange[0])
        self.SmoothedDirectionalMovementPlus.append(self._nz(self.SmoothedDirectionalMovementPlus, -1) - (self._nz(self.SmoothedDirectionalMovementPlus, -1) / 14) + self.DirectionalMovementPlus[-1])
        self.SmoothedDirectionalMovementMinus.append(self._nz(self.SmoothedDirectionalMovementMinus, -1) - (self._nz(self.SmoothedDirectionalMovementMinus, -1) / 14) + self.DirectionalMovementMinus[-1])
        self.DIPlus.append(self.SmoothedDirectionalMovementPlus[-1] / self.SmoothedTrueRange[-1] * 100)
        self.DIMinus.append(self.SmoothedDirectionalMovementMinus[-1] / self.SmoothedTrueRange[-1] * 100)
        if self.p.usedi is True:
            if self.DIPlus[-1] > self.DIMinus[-1]:
                self.DItrend.append(1)
            else:
                self.DItrend.append(-1)
        else:
            self.DItrend.append(0)

        # TTS method(Trend Trader Strategy)
        self.hiLimit = self.highestC[-1] - (self.avgTR[-1] * 3)
        self.loLimit = self.lowestC[-1] + (self.avgTR[-1] * 3)
        if self.data.close[0] > self.hiLimit and self.data.close[0] > self.loLimit:
            self.ret.append(self.hiLimit)
        else:
            if self.data.close[0] < self.loLimit and self.data.close[0] < self.hiLimit:
                self.ret.append(self.loLimit)
            else:
                self.ret.append(self._nz(self.ret, -1))
        if self.data.close[0] > self.ret[-1]:
            self.pos.append(1)
        else:
            if self.data.close[0] < self.ret[-1]:
                self.pos.append(-1)
            else:
                self.pos.append(self._nz(self.pos, -1))
        # End of HPotter 's code

        if self.p.usetts is True:
            if self.pos[-1] == 1:
                self.TTStrend.append(1)
            else:
                if self.pos[-1] == -1:
                    self.TTStrend.append(-1)
                else:
                    self.TTStrend.append(self.TTStrend[-1])
        else:
            self.TTStrend.append(0)

        # RSI method
        self.RSIMain = (self.RSI13 - 50) * 1.5
        if self.p.usersi is True:
            if self.RSIMain > -10:
                self.RSItrend.append(1)
            else:
                if self.RSIMain < 10:
                    self.RSItrend.append(-1)
                else:
                    self.RSItrend.append(self._nz(self.pos, -1))
        else:
            self.RSItrend.append(0)

        # WTO("WaveTrend Oscilator") method
        if self.p.usewto is True:
            if self.tci[0] > 0:
                self.WTOtrend.append(1)
            else:
                if self.tci[0] < 0:
                    self.WTOtrend.append(-1)
                else:
                    self.WTOtrend.append(0)
        else:
            self.WTOtrend.append(0)

        # plots
        self.trends.append(self.WOWtrend[-1] + self.BMAtrend[-1] + self.BARtrend[-1] + self.SUPtrend[-1] + self.DItrend[-1] + self.TTStrend[-1] + self.RSItrend[-1] + self.WTOtrend[-1])

        # arrows
        if self.trends[-1] >= self.p.sensup:
            self.posi.append(1)
        else:
            if self.trends[-1] <= (-1 * self.p.sensdn):
                self.posi.append(-1)
            else:
                self.posi.append(self.posi[-1])

        if self.posi[-1] == 1 and self.posi[-2] < 1:
            self.arr.append(1)
        else:
            if self.posi[-1] == -1 and self.posi[-2] > -1:
                self.arr.append(-1)
            else:
                self.arr.append(0)

        # locomotive
        if self.data.close[0] > self.data.open[0]:
            self.bar.append(1)
        else:
            if self.data.close[0] < self.data.open[0]:
                self.bar.append(-1)
            else:
                self.bar.append(0)
        if self.bar[-1] == -1 and self.bar[-2] == 1 and self.bar[-3] == 1:
            self.locotop.append(1)
        else:
            self.locotop.append(0)
        if self.bar[-1] == 1 and self.bar[-2] == -1 and self.bar[-3] == -1:
            self.locobot.append(1)
        else:
            self.locobot.append(0)
        if self.posi[-1] == self.posi[-2]:
            if (self.locotop[-1] == 1 and self.posi[-1] == -1) or (self.locobot[-1] == 1 and self.posi[-1] == 1):
                self.entry.append(1)
            else:
                self.entry.append(self.entry[-1])
        else:
            self.entry.append(0)

        self.uploco = True if self.locobot[-1] == 1 and self.entry[-2] == 0 and self.posi[-1] == 1 else False
        self.dnloco = True if self.locotop[-1] == 1 and self.entry[-2] == 0 and self.posi[-1] == -1 else False
        if self.p.uselocoentry is True:
            long_condition = self.uploco
        else:
            long_condition = True if self.arr[-1] == 1 else False

        if self.p.uselocoentry is True:
            short_condition = self.dnloco
        else:
            short_condition = True if self.arr[-1] == -1 else False

        # Signals
        self.is_open_long = True if long_condition else False
        self.is_close_long = True if short_condition else False
        self.is_open_short = True if short_condition else False
        self.is_close_short = True if long_condition else False

        if self.is_open_long is True and self.is_open_short is True:
            self.log('!!! Signals in opposite directions produced! is_open_long={}, is_open_short={}'.format(self.is_open_long, self.is_open_short))

    def print_strategy_debug_info(self):
        self.log('self.lasthigh = {}'.format(self.lasthigh[0]))
        self.log('self.lastlow = {}'.format(self.lastlow[0]))
        self.log('self.center = {}'.format(self.center[-1]))
        self.log('self.trend1 = {}'.format(self.trend1[-1]))
        self.log('self.trend2 = {}'.format(self.trend2[-1]))
        self.log('self.WOWtrend = {}'.format(self.WOWtrend[-1]))
        self.log('self.SMAOpen = {}'.format(self.SMAOpen[0]))
        self.log('self.SMAClose = {}'.format(self.SMAClose[0]))
        self.log('self.BMAtrend = {}'.format(self.BMAtrend[-1]))
        self.log('self.color = {}'.format(self.color[-1]))
        self.log('self.BARtrend = {}'.format(self.BARtrend[-1]))
        self.log('self.Atr3 = {}'.format(self.Atr3[0]))
        self.log('self.TrendUp = {}'.format(self.TrendUp[-1]))
        self.log('self.TrendDn = {}'.format(self.TrendDn[-1]))
        self.log('self.SUPtrend = {}'.format(self.SUPtrend[-1]))
        self.log('self.TrueRange = {}'.format(self.TrueRange[0]))
        self.log('self.DirectionalMovementPlus = {}'.format(self.DirectionalMovementPlus[-1]))
        self.log('self.DirectionalMovementMinus = {}'.format(self.DirectionalMovementMinus[-1]))
        self.log('self.SmoothedTrueRange = {}'.format(self.SmoothedTrueRange[-1]))
        self.log('self.SmoothedDirectionalMovementPlus = {}'.format(self.SmoothedDirectionalMovementPlus[-1]))
        self.log('self.SmoothedDirectionalMovementMinus = {}'.format(self.SmoothedDirectionalMovementMinus[-1]))
        self.log('self.DIPlus = {}'.format(self.DIPlus[-1]))
        self.log('self.DIMinus = {}'.format(self.DIMinus[-1]))
        self.log('self.DItrend = {}'.format(self.DItrend[-1]))
        self.log('self.Atr1 = {}'.format(self.Atr1[0]))
        self.log('self.avgTR = {}'.format(self.avgTR[0]))
        self.log('self.highestC = {}'.format(self.highestC[0]))
        self.log('self.lowestC = {}'.format(self.lowestC[0]))
        self.log('self.hiLimit = {}'.format(self.hiLimit))
        self.log('self.loLimit = {}'.format(self.loLimit))
        self.log('self.ret = {}'.format(self.ret[-1]))
        self.log('self.pos = {}'.format(self.pos[-1]))
        self.log('self.TTStrend = {}'.format(self.TTStrend[-1]))
        self.log('self.RSI13 = {}'.format(self.RSI13[0]))
        self.log('self.RSItrend = {}'.format(self.RSItrend[-1]))
        self.log('self.hlc3 = {}'.format(self.hlc3[0]))
        self.log('self.esa = {}'.format(self.esa[0]))
        self.log('self.hlc3esa = {}'.format(self.hlc3esa[0]))
        self.log('self.d = {}'.format(self.d[0]))
        self.log('self.ci = {}'.format(self.ci[0]))
        self.log('self.tci = {}'.format(self.tci[0]))
        self.log('self.WTOtrend = {}'.format(self.WTOtrend[-1]))
        self.log('self.trends = {}'.format(self.trends[-1]))
        self.log('self.posi = {}'.format(self.posi[-1]))
        self.log('self.arr = {}'.format(self.arr[-1]))
        self.log('self.bar = {}'.format(self.bar[-1]))
        self.log('self.locotop = {}'.format(self.locotop[-1]))
        self.log('self.locobot = {}'.format(self.locobot[-1]))
        self.log('self.entry = {}'.format(self.entry[-1]))
        self.log('self.uploco = {}'.format(self.uploco))
        self.log('self.dnloco = {}'.format(self.dnloco))

