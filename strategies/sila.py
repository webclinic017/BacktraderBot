import backtrader as bt
import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz

class AlexNoroSILAStrategy(bt.Strategy):
    '''
    This is an implementation of a strategy from TradingView - Alex (Noro) SILA v1.6.1L Strategy.
    '''

    strat_id = -1
    params = (
        ("debug", False),
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
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 12),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime()
        if self.p.debug:
            print('%s  %s' % (dt, txt))

    def getdaterange(self):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(self.p.fromyear, self.p.frommonth, self.p.fromday, self.p.toyear,
                                                      self.p.tomonth, self.p.today)
    def _nz(self, data_arr, idx):
        if len(data_arr) < (abs(idx) + 1):
            return 0
        else:
            return data_arr[idx]

    def __init__(self):
        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        self.curr_position = 0
        self.curtradeid = -1

        self.tradesopen = {}
        self.tradesclosed = {}

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

    def start(self):
        #print("start(): vars(self.p)={}".format(vars(self.p)))
        pass

    def next(self):
        # print("next(): id(self)={}".format(id(self)))

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
        long_condition = False
        if self.p.uselocoentry is True:
            long_condition = self.uploco
        else:
            long_condition = True if self.arr[-1] == 1 else False

        short_condition = False
        if self.p.uselocoentry is True:
            short_condition = self.dnloco
        else:
            short_condition = True if self.arr[-1] == -1 else False

        # Signals
        self.up1 = long_condition
        self.dn1 = short_condition
        self.is_up = True if self.up1 else False
        self.is_down = True if self.dn1 else False

        if self.is_up and self.is_down:
            self.log('!!! Signals in opposite directions produced! is_up={}, is_down={}'.format(self.is_up, self.is_down))

        # Trading
        self.fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        self.todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59, 59)
        self.currdt = self.data.datetime.datetime()

        self.gmt3_tz = pytz.timezone('Etc/GMT-3')
        self.fromdt = pytz.utc.localize(self.fromdt)
        self.todt = pytz.utc.localize(self.todt)
        self.currdt = self.gmt3_tz.localize(self.currdt, is_dst=True)

        self.printdebuginfonextinner()

        if self.is_up and self.currdt > self.fromdt and self.currdt < self.todt:
            if self.curr_position < 0:
                self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0:
                self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.buy(tradeid=self.curtradeid)
                self.curr_position = 1
                self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

        if self.is_down and self.currdt > self.fromdt and self.currdt < self.todt:
            if self.curr_position > 0:
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0:
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

    def notify_order(self, order):
        if order.status == order.Margin:
            self.log('notify_order() - ********** MARGIN CALL!! SKIP ORDER AND PREPARING FOR NEXT ORDERS!! **********')
            self.curr_position = 0

        self.log('notify_order() - Order Ref={}, Status={}, Broker Cash={}, self.position.size = {}'.format(order.ref, order.Status[order.status], self.broker.getcash(), self.position.size))

        if order.status in [bt.Order.Submitted]:
            return

        if order.status in [bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = 'BUY COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price, bt.num2date(order.executed.dt))
                self.log(buytxt)
            else:
                selltxt = 'SELL COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price, bt.num2date(order.executed.dt))
                self.log(selltxt)

        elif order.status in [order.Expired, order.Canceled]:
            pass  # Simply log

    def notify_trade(self, trade):
        self.log('!!! BEGIN notify_trade() - id(self)={}, self.curr_position={}, traderef={}, self.broker.getcash()={}'.format(id(self), self.curr_position, trade.ref, self.broker.getcash()))
        if trade.isclosed:
            self.tradesclosed[trade.ref] = trade
            self.log('---------------------------- TRADE CLOSED --------------------------')
            self.log("1: Data Name:                            {}".format(trade.data._name))
            self.log("2: Bar Num:                              {}".format(len(trade.data)))
            self.log("3: Current date:                         {}".format(self.data.datetime.date()))
            self.log('4: Status:                               Trade Complete')
            self.log('5: Ref:                                  {}'.format(trade.ref))
            self.log('6: PnL:                                  {}'.format(round(trade.pnl, 2)))
            self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))
            self.log('--------------------------------------------------------------------')
        elif trade.justopened:
            self.tradesopen[trade.ref] = trade
            self.log('TRADE JUST OPENED, SIZE={}, REF={}, VALUE={}, COMMISSION={}, BROKER CASH={}'.format(trade.size, trade.ref, trade.value, trade.commission, self.broker.getcash()))

    def printdebuginfonextinner(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        ddanalyzer = self.analyzers.dd.get_analysis()
        self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
        self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))
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
        self.log('self.curtradeid = {}'.format(self.curtradeid))
        self.log('self.uploco = {}'.format(self.uploco))
        self.log('self.dnloco = {}'.format(self.dnloco))
        self.log('self.up1 = {}'.format(self.up1))
        self.log('self.dn1 = {}'.format(self.dn1))
        self.log('self.is_up = {}'.format(self.is_up))
        self.log('self.is_down = {}'.format(self.is_down))
        self.log('----------------------')
