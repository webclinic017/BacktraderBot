import backtrader as bt
import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz


class AlexNoroRobotBitMEXFastRSIStrategy(bt.Strategy):
    '''
    This is an implementation of a strategy from TradingView - Alex (Noro) Robot BitMEX Fast RSI v1.0 strategy.
    '''

    strat_id = -1

    params = (
        ("debug", False),
        ("needlong", True),
        ("needshort", True),
        ("rsiperiod", 7),
        ("rsibars", 3),
        ("rsilong", 30),
        ("rsishort", 70),
        ("useocf", True),
        ("useccf", True),
        ("openbars", 3),
        ("closebars", 1),
        ("useobf", True),
        ("usecbf", True),
        ("openbody", 20),
        ("closebody", 20),
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
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(self.p.fromyear, self.p.frommonth, self.p.fromday, self.p.toyear, self.p.tomonth, self.p.today)


    def check_arr_equal(self, arr, val, last_num):
        cmp_arr = arr[len(arr) - last_num:len(arr)]
        return cmp_arr[0] == val and cmp_arr[1:] == cmp_arr[:-1]
        

    def __init__(self):
        self.curtradeid = -1
        self.curr_position = 0
        self.position_avg_price = 0

        self.tradesopen = {}
        self.tradesclosed = {}

        # RSI
        self.rsi = btind.RSI(self.data.close, period=self.p.rsiperiod, safediv=True)
        self.rsidn = [0] * 2
        self.rsiup = [0] * 2
        self.rsidnok = [0] * 2
        self.rsiupok = [0] * 2

        # Body Filter
        self.body = abs(self.data.close - self.data.open)
        self.abody = btind.SimpleMovingAverage(self.body, period=10)
        self.openbodyok = [0, 0]
        self.closebodyok = [0, 0]

        # Color Filter
        self.bar = [0] * 2
        self.gbar = [0] * 2
        self.rbar = [0] * 2

        self.check_gbar_openbars = [0] * 2
        self.check_rbar_openbars = [0] * 2
        self.check_gbar_closebars = [0] * 2
        self.check_rbar_closebars = [0] * 2 

        self.opengbarok = [0] * 2
        self.openrbarok = [0] * 2
        self.closegbarok = [0] * 2
        self.closerbarok = [0] * 2

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def start(self):
        # Check whether to skip this testing round
        # print("start(): id(self)={}".format(id(self)))
        if self.p.needlong is False and self.p.needshort is False:
            self.env.runstop()

    def next(self):
        # print("next(): id(self)={}".format(id(self)))
        # print("next() - Quick!")

        # RSI
        if self.rsi[0] < self.p.rsilong:
            self.rsidn.append(1)
        else:
            self.rsidn.append(0)
        if self.rsi[0] > self.p.rsishort:
            self.rsiup.append(1)
        else:
            self.rsiup.append(0)

        if self.check_arr_equal(self.rsidn, 1, self.p.rsibars):
            self.rsidnok.append(1)
        else:
            self.rsidnok.append(0)
        if self.check_arr_equal(self.rsiup, 1, self.p.rsibars):
            self.rsiupok.append(1)
        else:
            self.rsiupok.append(0)

        # Body Filter
        if self.body[0] >= self.abody[0] / 100 * self.p.openbody or self.p.useobf is False:
            self.openbodyok.append(1)
        else:
            self.openbodyok.append(0)
        if self.body[0] >= self.abody[0] / 100 * self.p.closebody or self.p.usecbf is False:
            self.closebodyok.append(1)
        else:
            self.closebodyok.append(0)

        # Color Filter
        if self.data.close[0] > self.data.open[0]:
            self.bar.append(1)
        else:
            if self.data.close[0] < self.data.open[0]:
                self.bar.append(-1)
            else:
                self.bar.append(0)

        if self.bar[-1] == 1:
            self.gbar.append(1)
        else:
            self.gbar.append(0)
        if self.bar[-1] == -1:
            self.rbar.append(1)
        else:
            self.rbar.append(0)

        self.check_gbar_openbars.append(self.check_arr_equal(self.gbar, 1, self.p.openbars))
        self.check_rbar_openbars.append(self.check_arr_equal(self.rbar, 1, self.p.openbars))
        self.check_gbar_closebars.append(self.check_arr_equal(self.gbar, 1, self.p.closebars)) 
        self.check_rbar_closebars.append(self.check_arr_equal(self.rbar, 1, self.p.closebars))

        if self.check_gbar_openbars[-1] is True or self.p.useocf is False:
            self.opengbarok.append(1)
        else:
            self.opengbarok.append(0)
        if self.check_rbar_openbars[-1] is True or self.p.useocf is False:
            self.openrbarok.append(1)
        else:
            self.openrbarok.append(0)
        if self.check_gbar_closebars[-1] is True or self.p.useccf is False:
            self.closegbarok.append(1)
        else:
            self.closegbarok.append(0)
        if self.check_rbar_closebars[-1] is True or self.p.useccf is False:
            self.closerbarok.append(1)
        else:
            self.closerbarok.append(0)

        # Signals
        self.up = self.openrbarok[-1] == 1 and self.rsidnok[-1] == 1 and self.openbodyok[-1] == 1 and (self.curr_position == 0 or self.data.close[0] < self.position_avg_price)
        self.dn = self.opengbarok[-1] == 1 and self.rsiupok[-1] == 1 and self.openbodyok[-1] == 1 and (self.curr_position == 0 or self.data.close[0] > self.position_avg_price)
        self.exit = ((self.curr_position > 0 and self.closegbarok[-1] == 1 and self.rsi[0] > self.p.rsilong) or
                     (self.curr_position < 0 and self.closerbarok[-1] == 1 and self.rsi[0] < self.p.rsishort)) and \
                      self.closebodyok[-1] == 1

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
            if self.curr_position < 0 and (self.up or self.exit):
                self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                self.position_avg_price = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.up and self.p.needlong and self.curr_position == 0:
                self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.buy(tradeid=self.curtradeid)
                self.curr_position = 1
                self.position_avg_price = self.data.close
                self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position > 0 and (self.dn or self.exit):
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                self.position_avg_price = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.dn and self.p.needshort and self.curr_position == 0:
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

    def notify_order(self, order):
        if order.status == order.Margin:
            self.log('notify_order() - ********** MARGIN CALL!! SKIP ORDER AND PREPARING FOR NEXT ORDERS!! **********')
            self.curr_position = 0
            self.position_avg_price = 0

        self.log('notify_order() - Order Ref={}, Status={}, Broker Cash={}, self.position.size = {}'.format(order.ref, order.Status[order.status], self.broker.getcash(), self.position.size))

        if order.status in [bt.Order.Submitted]:
            return

        if order.status in [bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = 'BUY COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price,
                                                                             bt.num2date(order.executed.dt))
                self.log(buytxt)
            else:
                selltxt = 'SELL COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price,
                                                                               bt.num2date(order.executed.dt))
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
        self.log('self.curtradeid = {}'.format(self.curtradeid))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.position_avg_price = {}'.format(self.position_avg_price))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.rsi = {}'.format(self.rsi[0]))
        self.log('self.rsidn = {}'.format(self.rsidn[-1]))
        self.log('self.rsiup = {}'.format(self.rsiup[-1]))
        self.log('self.rsidnok = {}'.format(self.rsidnok[-1]))
        self.log('self.rsiupok = {}'.format(self.rsiupok[-1]))
        self.log('self.body = {}'.format(self.body[0]))
        self.log('self.abody = {}'.format(self.abody[0]))
        self.log('self.openbodyok = {}'.format(self.openbodyok[-1]))
        self.log('self.closebodyok = {}'.format(self.closebodyok[-1]))
        self.log('self.bar = {}'.format(self.bar[-1]))
        self.log('self.gbar = {}'.format(self.gbar[-1]))
        self.log('self.rbar = {}'.format(self.rbar[-1]))
        self.log('self.check_gbar_openbars = {}'.format(self.check_gbar_openbars[-1]))
        self.log('self.check_rbar_openbars = {}'.format(self.check_rbar_openbars[-1]))
        self.log('self.check_gbar_closebars = {}'.format(self.check_gbar_closebars[-1]))
        self.log('self.check_rbar_closebars = {}'.format(self.check_rbar_closebars[-1]))
        self.log('self.opengbarok = {}'.format(self.opengbarok[-1]))
        self.log('self.openrbarok = {}'.format(self.openrbarok[-1]))
        self.log('self.closegbarok = {}'.format(self.closegbarok[-1]))
        self.log('self.closerbarok = {}'.format(self.closerbarok[-1]))
        self.log('-------------------------------------------------------------------')
