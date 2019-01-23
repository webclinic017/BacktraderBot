import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
from strategies.abstractstrategy import AbstractStrategy


class S004_AlexNoroBandsScalperStrategy(AbstractStrategy):
    '''
    This is an implementation of a strategy from TradingView - Alex (Noro) Bands Sclaper v1.6 strategy.
    '''

    params = (
        ("debug", False),
        ("needlong", True),
        ("needshort", True),
        ("takepercent", 0),
        ("needbe", True),
        ("needct", False),
        ("bodylen", 10),
        ("trb", 1),
        ("len", 20),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 10),
        ("tomonth", 10),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.is_up = False
        self.is_down = False

        # PriceChannel 1
        self.lasthigh = btind.Highest(self.data.close, period=self.p.len)
        self.lastlow = btind.Lowest(self.data.close, period=self.p.len)
        self.center = (self.lasthigh + self.lastlow) / 2

        # Distance
        self.dist = abs(self.data.close - self.center)
        self.distsma = btind.SimpleMovingAverage(self.dist, period=self.p.len)
        self.hd = [0, 0]
        self.ld = [0, 0]
        self.hd2 = [0, 0]
        self.ld2 = [0, 0]

        # Trend
        self.chd = [0] * 6
        self.cld = [0] * 6
        self.uptrend = [0] * 6
        self.dntrend = [0] * 6
        self.trend = [0] * 2

        # Body
        self.body = abs(self.data.close - self.data.open)
        self.smabody = btind.ExponentialMovingAverage(self.body, period=30) / 10 * self.p.bodylen

        self.bar = [0] * 3

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def start(self):
        # Check whether to skip this testing round
        # print("start(): id(self)={}".format(id(self)))
        if self.p.needlong == False and self.p.needshort == False:
            self.env.runstop()

    def next(self):
        # print("next(): id(self)={}".format(id(self)))
        # print("next() - Quick!")

        # Distance
        self.hd.append(self.center[0] + self.distsma[0])
        self.ld.append(self.center[0] - self.distsma[0])
        self.hd2.append(self.center[0] + self.distsma[0] * 2)
        self.ld2.append(self.center[0] - self.distsma[0] * 2)

        # Trend
        if self.data.close[0] > self.hd[-1]:
            self.chd.append(True)
        else:
            self.chd.append(False)
        if self.data.close[0] < self.ld[-1]:
            self.cld.append(True)
        else:
            self.cld.append(False)

        if self.p.trb == 1 and self.chd[-1] is True:
            self.uptrend.append(1)
        else:
            if self.p.trb == 2 and self.chd[-1] is True and self.chd[-2] is True:
                self.uptrend.append(1)
            else:
                if self.p.trb == 3 and self.chd[-1] is True and self.chd[-2] is True and self.chd[-3] is True:
                    self.uptrend.append(1)
                else:
                    if self.p.trb == 4 and self.chd[-1] is True and self.chd[-2] is True and self.chd[-3] is True and self.chd[-4] is True:
                        self.uptrend.append(1)
                    else:
                        if self.p.trb == 5 and self.chd[-1] is True and self.chd[-2] is True and self.chd[-3] is True and self.chd[-4] is True and self.chd[-5] is True:
                            self.uptrend.append(1)
                        else:
                            self.uptrend.append(0)
        if self.p.trb == 1 and self.cld[-1] is True:
            self.dntrend.append(1)
        else:
            if self.p.trb == 2 and self.cld[-1] is True and self.cld[-2] is True:
                self.dntrend.append(1)
            else:
                if self.p.trb == 3 and self.cld[-1] is True and self.cld[-2] is True and self.cld[-3] is True:
                    self.dntrend.append(1)
                else:
                    if self.p.trb == 4 and self.cld[-1] is True and self.cld[-2] is True and self.cld[-3] is True and self.cld[-4] is True:
                        self.dntrend.append(1)
                    else:
                        if self.p.trb == 5 and self.cld[-1] is True and self.cld[-2] is True and self.cld[-3] is True and self.cld[-4] is True and self.cld[-5] is True:
                            self.dntrend.append(1)
                        else:
                            self.dntrend.append(0)

        if self.dntrend[-1] == 1 and self.data.high[0] < self.center[0]:
            self.trend.append(-1)
        else:
            if self.uptrend[-1] == 1 and self.data.low[0] > self.center[0]:
                self.trend.append(1)
            else:
                self.trend.append(self.trend[-1])

        # Signals
        if self.data.close[0] > self.data.open[0]:
            self.bar.append(1)
        else:
            if self.data.close[0] < self.data.open[0]:
                self.bar.append(-1)
            else:
                self.bar.append(0)

        # Signals
        self.up7 = 1 if self.trend[-1] == 1  and ((self.bar[-1] == -1 and self.bar[-2] == -1) or (self.body[0] > self.smabody[0] and self.bar[-1] == -1)) else 0
        self.dn7 = 1 if self.trend[-1] == 1  and ((self.bar[-1] == 1  and self.bar[-2] == 1)  or (self.data.close[0] > self.hd[-1] and self.p.needbe is True)) and self.data.close[0] > self.position_avg_price * (100 + self.p.takepercent) / 100 else 0
        self.up8 = 1 if self.trend[-1] == -1 and ((self.bar[-1] == -1 and self.bar[-2] == -1) or (self.data.close[0] < self.ld2[-1] and self.p.needbe is True)) and self.data.close[0] < self.position_avg_price * (100 - self.p.takepercent) / 100 else 0
        self.dn8 = 1 if self.trend[-1] == -1 and ((self.bar[-1] == 1  and self.bar[-2] == 1)  or (self.body[0] > self.smabody[0] and self.bar[-1] == 1)) else 0

        self.is_up = True if self.up7 == 1 or self.up8 == 1 else False
        self.is_down = True if self.dn7 == 1 or self.dn8 == 1 else False

        # Trading
        self.fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        self.todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59, 59)
        self.currdt = self.data.datetime.datetime()

        self.gmt3_tz = pytz.timezone('Etc/GMT-3')
        self.fromdt = pytz.utc.localize(self.fromdt)
        self.todt = pytz.utc.localize(self.todt)
        self.currdt = self.gmt3_tz.localize(self.currdt, is_dst=True)

        self.printdebuginfonextinner()

        if self.currdt > self.fromdt and self.currdt < self.todt:
            if self.curr_position < 0 and self.is_up is True:
                self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                self.position_avg_price = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.is_up is True and self.p.needlong is True and not (self.trend[-1] == -1 and self.p.needct is False):
                self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.buy(tradeid=self.curtradeid)
                self.curr_position = 1
                self.position_avg_price = self.data.close
                self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position > 0 and self.is_down is True:
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                self.position_avg_price = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.is_down is True and self.p.needshort is True and not (self.trend[-1] == 1 and self.p.needct is False):
                self.log('!!! BEFORE OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.sell(tradeid=self.curtradeid)
                self.curr_position = -1
                self.position_avg_price = self.data.close
                self.log('!!! AFTER OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

        if self.currdt > self.todt:
            self.log('!!! Time passed beyond date range')
            if self.curr_position != 0:  # if 'curtradeid' in self:
                self.log('!!! Closing trade prematurely')
                self.close(tradeid=self.curtradeid)
            self.curr_position = 0
            self.position_avg_price = 0

    def printdebuginfonextinner(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        ddanalyzer = self.analyzers.dd.get_analysis()
        self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
        self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.is_up = {}'.format(self.is_up))
        self.log('self.is_down = {}'.format(self.is_down))
        self.log('self.lasthigh[0] = {}'.format(self.lasthigh[0]))
        self.log('self.lastlow[0] = {}'.format(self.lastlow[0]))
        self.log('self.center[0] = {}'.format(self.center[0]))
        self.log('self.dist[0] = {}'.format(self.dist[0]))
        self.log('self.distsma[0] = {}'.format(self.distsma[0]))
        self.log('self.hd[-1] = {}'.format(self.hd[-1]))
        self.log('self.ld[-1] = {}'.format(self.ld[-1]))
        self.log('self.hd2[-1] = {}'.format(self.hd2[-1]))
        self.log('self.ld2[-1] = {}'.format(self.ld2[-1]))
        self.log('self.chd[-1] = {}'.format(self.chd[-1]))
        self.log('self.cld[-1] = {}'.format(self.cld[-1]))
        self.log('self.uptrend[-1] = {}'.format(self.uptrend[-1]))
        self.log('self.dntrend[-1] = {}'.format(self.dntrend[-1]))
        self.log('self.trend[-1] = {}'.format(self.trend[-1]))
        self.log('self.body[0] = {}'.format(self.body[0]))
        self.log('self.smabody[0] = {}'.format(self.smabody[0]))
        self.log('self.bar[-1] = {}'.format(self.bar[-1]))
        self.log('----------------------')
