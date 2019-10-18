import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S004_AlexNoroBandsScalperStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S004 Alex (Noro) Bands Sclaper v1.6 strategy.
    '''

    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("takepercent", 0),
        ("needbe", True),
        ("needct", False),
        ("bodylen", 10),
        ("trb", 1),
        ("len", 20),
        ("sl", None),
        ("tslflag", None),
        ("tp", None),
        ("ttpdist", None),
        ("tbdist", None),
        ("numdca", None),
        ("dcainterval", None),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 10),
        ("tomonth", 10),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.up7 = 0
        self.dn7 = 0
        self.up8 = 0
        self.dn8 = 0

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

    def calculate_signals(self):
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
        self.dn7 = 1 if self.trend[-1] == 1  and ((self.bar[-1] == 1  and self.bar[-2] == 1)  or (self.data.close[0] > self.hd[-1] and self.p.needbe is True)) and self.curr_position != 0 and self.data.close[0] > self.position_avg_price * (100 + self.p.takepercent) / 100 else 0
        self.up8 = 1 if self.trend[-1] == -1 and ((self.bar[-1] == -1 and self.bar[-2] == -1) or (self.data.close[0] < self.ld2[-1] and self.p.needbe is True)) and self.curr_position != 0 and self.data.close[0] < self.position_avg_price * (100 - self.p.takepercent) / 100 else 0
        self.dn8 = 1 if self.trend[-1] == -1 and ((self.bar[-1] == 1  and self.bar[-2] == 1)  or (self.body[0] > self.smabody[0] and self.bar[-1] == 1)) else 0

        self.is_open_long = True if (self.up7 == 1 or self.up8 == 1) and not (self.trend[-1] == -1 and self.p.needct is False) else False
        self.is_close_long = True if self.position.size > 0 and (self.dn7 == 1 or self.dn8 == 1) else False
        self.is_open_short = True if (self.dn7 == 1 or self.dn8 == 1) and not (self.trend[-1] == 1 and self.p.needct is False) else False
        self.is_close_short = True if self.position.size < 0 and (self.up7 == 1 or self.up8 == 1) else False

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
            self.log('!!! Changed signals as follows: is_open_long={}, is_open_short={}'.format(self.is_open_long, self.is_open_short))

    def printdebuginfo(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        if not self.islivedata():
            ddanalyzer = self.analyzers.dd.get_analysis()
            self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
            self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
            self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
            self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.pending_order.ref = {}'.format(self.get_pending_order_ref()))
        self.log('self.curtradeid = {}'.format(self.curtradeid))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.position_avg_price = {}'.format(self.position_avg_price))
        self.log('self.data.datetime[0] = {}'.format(self.data.datetime.datetime()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))
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
        self.log('self.p.needct = {}'.format(self.p.needct))
        self.log('self.body[0] = {}'.format(self.body[0]))
        self.log('self.smabody[0] = {}'.format(self.smabody[0]))
        self.log('self.bar[-1] = {}'.format(self.bar[-1]))
        self.log('self.bar[-2] = {}'.format(self.bar[-2]))
        self.log('self.up7 = {}'.format(self.up7))
        self.log('self.dn7 = {}'.format(self.dn7))
        self.log('self.up8 = {}'.format(self.up8))
        self.log('self.dn8 = {}'.format(self.dn8))
        self.log('self.is_open_long = {}'.format(self.is_open_long))
        self.log('self.is_close_long = {}'.format(self.is_close_long))
        self.log('self.is_open_short = {}'.format(self.is_open_short))
        self.log('self.is_close_short = {}'.format(self.is_close_short))
        self.log('-------------------------------------------------------------------')
