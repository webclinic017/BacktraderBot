import backtrader as bt
import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
import sys

class AlexNoroTrendMAsStrategy(bt.Strategy):
    '''
    This is an implementation of a strategy from TradingView - Alex (Noro) TrendMAs strategy.
    '''

    strat_id = -1

    params = (
        ("debug", False),
        ("needlong", True),
        ("needshort", True),
        ("needstops", True),
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
        ("step1_key", ""),
    )
 
    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime()
        print('%s  %s' % (dt, txt))

    def getdaterange(self):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(self.p.fromyear, self.p.frommonth, self.p.fromday, self.p.toyear, self.p.tomonth, self.p.today)

    def __init__(self):
        self.curr_position = 0
        
        self.tradesopen = {}
        self.tradesclosed = {}

        self.stoploss_order = None

        #self.rsi       = bt.talib.RSI(self.data.close, timeperiod=2)
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
        self.stoplong  = [0.0, 0.0]
        self.stopshort = [0.0, 0.0]

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def start(self):
        # Check whether to skip this testing round
        print("start(): id(self)={}, self.p.step1_key={}".format(id(self), self.p.step1_key))
        if(self.p.needlong == False and self.p.needshort == False):
            self.env.runstop()

    def next(self):   
        #print("next(): id(self)={}, self.p.step1_key={}".format(id(self), self.p.step1_key))
        #print("next() - Quick!")
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
        self.up1 = True if self.trend[-1] == 1 and (self.data.low[0] < self.center2[-1] or self.p.usefastsma == False) and self.redbars[-1] == 1 else False
        self.up2 = True if self.data.high[0] < self.center[-1] and self.data.high[0] < self.center2[-1] and self.bar[-1] == -1 and self.p.needex == True else False
        self.up3 = 1 if self.data.close[0] < self.data.open[0] and self.len[0] > self.sma[0] * 3 and self.minV[0] < self.minV[-1] and self.fastrsi < 10 else 0
        self.dn1 = True if self.trend[-1] == -1 and (self.data.high[0] > self.center2[-1] or self.p.usefastsma == False) and self.greenbars[-1] == 1 else False
        self.dn2 = True if self.data.low[0] > self.center[-1] and self.data.low[0] > self.center2[-1] and self.bar[-1] == 1 and self.p.needex == True else False
        is_up = True if self.up1 or self.up2 or self.up3 == 1 else False
        is_down = True if self.dn1 else False

        if(is_up and is_down):
            if(self.p.debug):
                self.log('!!! Signals in opposite directions produced! is_up={}, is_down={}'.format(is_up, is_down))
            if(self.position.size < 0):
                is_up = True
                is_down = False
            if(self.position.size > 0):
                is_up = False
                is_down = True
            if(self.position.size == 0):
                is_up = True if self.p.needlong and not self.p.needshort or self.p.needlong and self.p.needshort else False
                is_down = True if not self.p.needlong and self.p.needshort else False
            if(self.p.debug):
                self.log('!!! Changed signals as follows: is_up={}, is_down={}'.format(is_up, is_down))

        #Trading
        if self.up1 == 1 and self.p.needstops == True:
            self.stoplong.append(self.data.close - (self.data.close / 100 * self.p.stoppercent))
        else: 
            self.stoplong.append(self.stoplong[-2])

        if self.dn1 == 1 and self.p.needstops == True:
            self.stopshort.append(self.data.close + (self.data.close / 100 * self.p.stoppercent))
        else: 
            self.stopshort.append(self.stopshort[-2])

        self.fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        self.todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59, 59)
        self.currdt = self.data.datetime.datetime()

        self.gmt3_tz = pytz.timezone('Etc/GMT-3')
        self.fromdt = pytz.utc.localize(self.fromdt)
        self.todt = pytz.utc.localize(self.todt)
        self.currdt = self.gmt3_tz.localize(self.currdt, is_dst=True)

        self.printdebuginfonextinner()

        if is_up and self.currdt > self.fromdt and self.currdt < self.todt:
            if self.curr_position < 0:
                if self.p.debug:
                    self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                self.cancel_stoploss_orders()
                ddanalyzer = self.analyzers.dd            
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0) # Notify DrawDown analyzer separately  
                if self.p.debug:
                    self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.p.needlong and self.curr_position == 0:
                if self.p.debug:
                    self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                if(self.p.needstops == False):
                    self.buy(tradeid=self.curtradeid)
                else:
                    mainside_order = self.buy(tradeid=self.curtradeid, exectype=bt.Order.Limit, transmit=False)
                    self.stoploss_order = self.sell(price=self.stoplong[-1], tradeid=self.curtradeid, exectype=bt.Order.Stop, transmit=True, parent=mainside_order)
                self.curr_position = 1
                if self.p.debug:
                    self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                    
        if is_down and self.currdt > self.fromdt and self.currdt < self.todt:
            if self.curr_position > 0:
                if self.p.debug:
                    self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                self.cancel_stoploss_orders()
                ddanalyzer = self.analyzers.dd            
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0) # Notify DrawDown analyzer separately  
                if self.p.debug:
                    self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.p.needshort and self.curr_position == 0:
                if self.p.debug:
                    self.log('!!! BEFORE OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                if(self.p.needstops == False):
                    self.sell(tradeid=self.curtradeid)
                else:
                    mainside_s_order = self.sell(tradeid=self.curtradeid, exectype=bt.Order.Limit, transmit=False)
                    self.stoploss_order = self.buy(price=self.stopshort[-1], tradeid=self.curtradeid, exectype=bt.Order.Stop, transmit=True, parent=mainside_s_order)
                self.curr_position = -1
                if self.p.debug:
                    self.log('!!! AFTER OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

        if self.currdt > self.todt:
            if self.p.debug:
                self.log('!!! Time passed beyond date range')
            if self.curr_position != 0: #if 'curtradeid' in self:
                if self.p.debug:
                    self.log('!!! Closing trade prematurely')
                self.close(tradeid=self.curtradeid)
            self.cancel_stoploss_orders()
            self.curr_position = 0

    def cancel_stoploss_orders(self):
        if(self.p.needstops == True and self.stoploss_order):
            if self.p.debug:
                self.log('!!! Inside cancel_stoploss_orders(). self.stoploss_order={}'.format(self.stoploss_order))
            self.cancel(self.stoploss_order)
            self.stoploss_order = None

    def notify_order(self, order):
        if order.status == order.Margin:
            if self.p.debug:
                self.log('notify_order() - ********** MARGIN CALL!! SKIP ORDER AND PREPARING FOR NEXT ORDERS!! **********')
            self.curr_position = 0
            self.cancel_stoploss_orders()
        
        if self.p.debug:
            self.log('notify_order() - Order Ref={}, Status={}, Broker Cash={}, self.position.size = {}'.format(order.ref, order.Status[order.status], self.broker.getcash(), self.position.size))

        if order.status in [bt.Order.Submitted]:
            return

        if order.status in [bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if(self.stoploss_order and order.ref == self.stoploss_order.ref):
                if self.p.debug:
                    self.log('Setting self.stoploss_order=None')
                self.stoploss_order = None
            if order.isbuy():
                if self.p.debug:
                    buytxt = 'BUY COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price, bt.num2date(order.executed.dt))
                    self.log(buytxt)
            else:
                if self.p.debug:
                    selltxt = 'SELL COMPLETE, Order Ref={}, {} - at {}'.format(order.ref, order.executed.price, bt.num2date(order.executed.dt))
                    self.log(selltxt)

        elif order.status in [order.Expired, order.Canceled]:
            pass  # Simply log

    def notify_trade(self, trade):
        if self.p.debug:
            self.log('!!! BEGIN notify_trade() - id(self)={}, self.curr_position={}, traderef={}, self.broker.getcash()={}'.format(id(self), self.curr_position, trade.ref, self.broker.getcash()))
        if trade.isclosed:
            self.tradesclosed[trade.ref] = trade       
            if self.p.debug:
                self.log('---------------------------- TRADE CLOSED --------------------------')
                self.log("1: Data Name:                            {}".format(trade.data._name))
                self.log("2: Bar Num:                              {}".format(len(trade.data)))
                self.log("3: Current date:                         {}".format(self.data.datetime.date()))
                self.log('4: Status:                               Trade Complete')
                self.log('5: Ref:                                  {}'.format(trade.ref))
                self.log('6: PnL:                                  {}'.format(round(trade.pnl,2)))
                self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))
                self.log('--------------------------------------------------------------------')

        elif trade.justopened:
            self.tradesopen[trade.ref] = trade
            if self.p.debug:
                self.log('TRADE JUST OPENED, SIZE={}, REF={}, VALUE={}, COMMISSION={}, BROKER CASH={}'.format(trade.size, trade.ref, trade.value, trade.commission, self.broker.getcash()))

    def printdebuginfonextinner(self):
        if self.p.debug:
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
            self.log('self.stoplong = {}'.format(self.stoplong[-1]))
            self.log('self.stopshort = {}'.format(self.stopshort[-1]))
            self.log('up1 = {} - True if self.trend[-1]({}) == 1 and (self.data.low[0]({}) < self.center2[-1]({}) or self.p.usefastsma({}) == False) and self.redbars[-1]({}) == 1 else False'.format(self.up1, self.trend[-1], self.data.low[0], self.center2[-1], self.p.usefastsma, self.redbars[-1]))
            self.log('dn1 = {} - True if self.trend[-1]({}) == -1 and (self.data.high[0]({}) > self.center2[-1]({}) or self.p.usefastsma({}) == False) and self.greenbars[-1]({}) == 1 else False'.format(self.dn1, self.trend[-1], self.data.high[0], self.center2[-1], self.p.usefastsma, self.greenbars[-1]))
            self.log('up2 = {} - True if self.data.high[0]({}) < self.center[-1]({}) and self.data.high[0]({}) < self.center2[-1]({}) and self.bar[-1]({}) == -1 and self.p.needex({}) == True else False'.format(self.up2, self.data.high[0], self.center[-1], self.data.high[0], self.center2[-1], self.bar[-1], self.p.needex))
            self.log('dn2 = {}'.format(self.dn2))
            self.log('up3 = {} - 1 if self.data.close[0]({}) < self.data.open[0]({}) and self.len[0]({}) > self.sma[0]({}) * 3 and self.minV[0]({}) < self.minV[-1]({}) and fastrsi({}) < 10 else 0'.format(self.up3, self.data.close[0], self.data.open[0], self.len[0], self.sma[0], self.minV[0], self.minV[-1], self.fastrsi))
            self.log('----------------------')
