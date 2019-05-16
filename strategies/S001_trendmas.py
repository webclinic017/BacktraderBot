import backtrader as bt
import backtrader.indicators as btind
from strategies.abstractstrategy import AbstractStrategy


class S001_AlexNoroTrendMAsStrategy(AbstractStrategy):
    '''
    This is an implementation of a strategy from TradingView - S001 Alex (Noro) TrendMAs v2.3 strategy.
    '''

    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("needstops", False),
        ("stoppercent", 5),
        ("usefastsma", True),
        ("fastlen", 3),
        ("slowlen", 21),
        ("bars", 0),
        ("needex", True),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 10),
        ("tomonth", 10),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.rsi       = btind.RSI(self.data.close, period=2, safediv=True)
        self.lasthigh  = btind.Highest(self.data.close, period=self.p.slowlen)
        self.lastlow   = btind.Lowest(self.data.close, period=self.p.slowlen)
        self.lasthigh2 = btind.Highest(self.data.close, period=self.p.fastlen)
        self.lastlow2  = btind.Lowest(self.data.close, period=self.p.fastlen)
        self.trend     = [0, 0]
        self.center    = [0.0]
        self.center2   = [0.0]
        self.bar       = [0, 0, 0]
        self.redbars   = [0]
        self.greenbars = [0]

        #CryptoBottom
        self.mac       = btind.SimpleMovingAverage(self.data.close, period=10)
        self.len       = abs(self.data.close - self.mac)
        self.sma       = btind.SimpleMovingAverage(self.len, period=100)
        self.maxV      = bt.Max(self.data.open, self.data.close)
        self.minV      = bt.Min(self.data.open, self.data.close)

    def calculate_signals(self):
        #PriceChannel 1
        self.center.append((self.lasthigh[0] + self.lastlow[0]) / 2)

        #PriceChannel 2
        self.center2.append((self.lasthigh2[0] + self.lastlow2[0]) / 2)

        #Trend
        if self.data.low[0] > self.center[-1] and self.data.low[-1] > self.center[-2]:
            self.trend.append(1)
        else: 
            if self.data.high[0] < self.center[-1] and self.data.high[-1] < self.center[-2]: 
                self.trend.append(-1)
            else:
                self.trend.append(self.trend[-1])

        #Bars
        if self.data.close[0] > self.data.open[0]:
            self.bar.append(1)
        else: 
            if self.data.close[0] < self.data.open[0]: 
                self.bar.append(-1)
            else:
                self.bar.append(0)

        if self.p.bars == 0:
            self.redbars.append(1)
        else: 
            if self.p.bars == 1 and self.bar[-1] == -1: 
                self.redbars.append(1)
            else:
                if self.p.bars == 2 and self.bar[-1] == -1 and self.bar[-2] == -1: 
                    self.redbars.append(1)
                else:
                    if self.p.bars == 3 and self.bar[-1] == -1 and self.bar[-2] == -1 and self.bar[-3] == -1: 
                        self.redbars.append(1)
                    else:
                        self.redbars.append(0)

        if self.p.bars == 0:
            self.greenbars.append(1)
        else: 
            if self.p.bars == 1 and self.bar[-1] == 1: 
                self.greenbars.append(1)
            else:
                if self.p.bars == 2 and self.bar[-1] == 1 and self.bar[-2] == 1: 
                    self.greenbars.append(1)
                else:
                    if self.p.bars == 3 and self.bar[-1] == 1 and self.bar[-2] == 1 and self.bar[-3] == 1: 
                        self.greenbars.append(1)
                    else:
                        self.greenbars.append(0)

        #Fast RSI
        self.fastrsi = self.rsi[0]

        #Signals
        self.up1 = True if self.trend[-1] == 1 and (self.data.low[0] < self.center2[-1] or self.p.usefastsma is False) and self.redbars[-1] == 1 else False
        self.up2 = True if self.data.high[0] < self.center[-1] and self.data.high[0] < self.center2[-1] and self.bar[-1] == -1 and self.p.needex is True else False
        self.up3 = 1 if self.data.close[0] < self.data.open[0] and self.len[0] > self.sma[0] * 3 and self.minV[0] < self.minV[-1] and self.fastrsi < 10 else 0
        self.dn1 = True if self.trend[-1] == -1 and (self.data.high[0] > self.center2[-1] or self.p.usefastsma is False) and self.greenbars[-1] == 1 else False
        self.dn2 = True if self.data.low[0] > self.center[-1] and self.data.low[0] > self.center2[-1] and self.bar[-1] == 1 and self.p.needex is True else False

        self.is_open_long = True if self.up1 or self.up2 or self.up3 == 1 else False
        self.is_close_long = True if self.dn1 else False
        self.is_open_short = True if self.dn1 else False
        self.is_close_short = True if self.up1 or self.up2 or self.up3 == 1 else False

        if self.is_open_long is True and self.is_open_short is True:
            self.log('!!! Signals in opposite directions produced! is_open_long={}, is_open_short={}'.format(self.is_open_long, self.is_open_short))
            if self.position.size < 0:
                self.is_open_long = True
                self.is_close_long = False
                self.is_open_short = False
                self.is_close_short = True
            if self.position.size > 0:
                self.is_open_long = False
                self.is_close_long = True
                self.is_open_short = True
                self.is_close_short = False
            if self.position.size == 0:
                self.is_open_long = True if self.p.needlong and not self.p.needshort or self.p.needlong and self.p.needshort else False
                self.is_close_long = False
                self.is_open_short = True if not self.p.needlong and self.p.needshort else False
                self.is_close_short = False
            self.log('!!! Changed signals as follows: self.is_open_long={}, self.is_open_short={}'.format(self.is_open_long, self.is_open_short))

    def printdebuginfonextinner(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        ddanalyzer = self.analyzers.dd.get_analysis()
        self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
        self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.rsi = {}'.format(self.rsi[0]))
        self.log('self.data.open[0] = {}'.format(self.data.open[0]))
        self.log('self.data.high[0]= {}'.format(self.data.high[0]))
        self.log('self.data.low[0] = {}'.format(self.data.low[0]))
        self.log('self.data.close[0] = {}'.format(self.data.close[0]))
        self.log('self.lasthigh = {}'.format(self.lasthigh[0]))
        self.log('self.lastlow = {}'.format(self.lastlow[0]))
        self.log('self.lasthigh2 = {}'.format(self.lasthigh2[0]))
        self.log('self.lastlow2 = {}'.format(self.lastlow2[0]))
        self.log('self.trend = {}'.format(self.trend[-1]))
        self.log('self.center = {}'.format(self.center[-1]))
        self.log('self.center2 = {}'.format(self.center2[-1]))
        self.log('self.bar = {}'.format(self.bar[-1]))
        self.log('self.redbars = {}'.format(self.redbars[-1]))
        self.log('self.greenbars = {}'.format(self.greenbars[-1]))
        self.log('self.mac = {}'.format(self.mac[0]))
        self.log('self.len = {}'.format(self.len[0]))
        self.log('self.sma = {}'.format(self.sma[0]))
        self.log('self.maxV = {}'.format(self.maxV[0]))
        self.log('self.minV = {}'.format(self.minV[0]))
        self.log('up1 = {} - True if self.trend[-1]({}) == 1 and (self.data.low[0]({}) < self.center2[-1]({}) or self.p.usefastsma({}) == False) and self.redbars[-1]({}) == 1 else False'.format(self.up1, self.trend[-1], self.data.low[0], self.center2[-1], self.p.usefastsma, self.redbars[-1]))
        self.log('dn1 = {} - True if self.trend[-1]({}) == -1 and (self.data.high[0]({}) > self.center2[-1]({}) or self.p.usefastsma({}) == False) and self.greenbars[-1]({}) == 1 else False'.format(self.dn1, self.trend[-1], self.data.high[0], self.center2[-1], self.p.usefastsma, self.greenbars[-1]))
        self.log('up2 = {} - True if self.data.high[0]({}) < self.center[-1]({}) and self.data.high[0]({}) < self.center2[-1]({}) and self.bar[-1]({}) == -1 and self.p.needex({}) == True else False'.format(self.up2, self.data.high[0], self.center[-1], self.data.high[0], self.center2[-1], self.bar[-1], self.p.needex))
        self.log('dn2 = {}'.format(self.dn2))
        self.log('up3 = {} - 1 if self.data.close[0]({}) < self.data.open[0]({}) and self.len[0]({}) > self.sma[0]({}) * 3 and self.minV[0]({}) < self.minV[-1]({}) and fastrsi({}) < 10 else 0'.format(self.up3, self.data.close[0], self.data.open[0], self.len[0], self.sma[0], self.minV[0], self.minV[-1], self.fastrsi))
        self.log('self.is_open_long = {}'.format(self.is_open_long))
        self.log('self.is_close_long = {}'.format(self.is_close_long))
        self.log('self.is_open_short = {}'.format(self.is_open_short))
        self.log('self.is_close_short = {}'.format(self.is_close_short))
        self.log('----------------------')
