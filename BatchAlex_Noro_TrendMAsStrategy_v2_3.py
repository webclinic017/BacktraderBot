'''
Batch testing of the implementation of the TradingView strategy: Alex(Noro) Trend MAs v2.3
'''
 
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from datetime import datetime
import math
import argparse
from backtrader import TimeFrame
import itertools
import pytz
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer 

tradesopen = {}
tradesclosed = {}
batch_number = 0

def parse_args():
    parser = argparse.ArgumentParser(description='Alex(Noro) Trend MAs v2.3 Strategy')
 
    parser.add_argument('--commsizer',
                            action ='store_true',help=('Use the Sizer '
                                'that takes commissions into account'))
 
    parser.add_argument('--commtype',
                        default="Percentage",
                        type=str,
                        choices=["Percentage", "Fixed"],
                        help='The type of commission to apply to a trade')
 
    parser.add_argument('--commission',
                        default=0.001,
                        type=float,
                        help='The amount of commission to apply to a trade')
 
    parser.add_argument('--risk',
                        default=0.02,
                        type=float,
                        help='The percentage of available cash to risk on a trade')
 
    parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Debugs'))
 
    return parser.parse_args()
 
 
 
class maxRiskSizer(bt.Sizer):
    '''
    Returns the number of shares rounded down that can be purchased for the
    max risk tolerance
    '''
    params = (('risk', 0.1),
              ('debug', True))
 
    def _getsizing(self, comminfo, cash, data, isbuy):
 
        max_risk =  math.floor(cash * self.p.risk)
 
        if isbuy == True:
            size = max_risk / data[0]
        else:
            size = max_risk / data[0] * -1
 
        #Finally round down to the nearest unit
        size = math.floor(size)
 
        if self.p.debug:
            if isbuy:
                buysell = 'Buying'
            else:
                buysell = 'Selling'
            print("------------- Sizer Debug --------------")
            print("Action: {}".format(buysell))
            print("Price: {}".format(data[0]))
            print("Cash: {}".format(cash))
            print("Max Risk %: {}".format(self.p.risk))
            print("Max Risk $: {}".format(max_risk))
            print("Current Price: {}".format(data[0]))
            print("Size: {}".format(size))
            print("----------------------------------------")
        return size
 
 
class maxRiskSizerComms(bt.Sizer):
    '''
    Returns the number of shares rounded down that can be purchased for the
    max risk tolerance
    '''
    params = (('risk', 0.1),
                ('debug', True))
 
    def _getsizing(self, comminfo, cash, data, isbuy):
        size = 0
 
        # Work out the maximum size assuming all cash can be used.
        max_risk = math.floor(cash * self.p.risk)
 
        comm = comminfo.p.commission
 
        if comminfo.stocklike: # We are using a percentage based commissions
 
            # Apply the commission to the price. We can then divide our risk
            # by this value
            com_adj_price = data[0] * (1 + (comm * 2)) # *2 for round trip
            comm_adj_max_risk = "N/A"
 
            if isbuy == True:
                comm_adj_size = max_risk / com_adj_price
                if comm_adj_size < 0: #Avoid accidentally going short
                    comm_adj_size = 0
            else:
                comm_adj_size = max_risk / com_adj_price * -1
 
        #Finally make sure we round down to the nearest unit.
        comm_adj_size = math.floor(comm_adj_size)
 
        if self.p.debug:
            if isbuy:
                buysell = 'Buying'
            else:
                buysell = 'Selling'
            print("------------- Sizer Debug --------------")
            print("Action: {}".format(buysell))
            print("Price: {}".format(data[0]))
            print("Cash: {}".format(cash))
            print("Max Risk %: {}".format(self.p.risk))
            print("Max Risk $: {}".format(max_risk))
            print("Current Price: {}".format(data[0]))
            print("Commission: {}".format(comm))
            print("Commission Adj Price (Round Trip): {}".format(com_adj_price))
            print("Size: {}".format(comm_adj_size))
            print("----------------------------------------")
        return comm_adj_size

 
class BatchAlexNoroTrendMAsStrategy(bt.Strategy):
    '''
    This is a strategy from TradingView - Alex (Noro) TrendMAs strategy.
    '''
    params = (
        ("needlong", True),
        ("needshort", True),
        ("needstops", False),
        ("stoppercent", 5),
        ("usefastsma", True),
        ("fastlen", 5),
        ("slowlen", 21),
        ("bars", 2),
        ("needex", False),
        ("fromyear", 2018),
        ("toyear", 2118),
        ("frommonth", 10),
        ("tomonth", 10),
        ("fromday", 3),
        ("today", 31),
    )
 
    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime()
        print('%s  %s' % (dt, txt))

    def __init__(self):
        self.curr_position = 0

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
        self.stoplong  = [0.0]
        self.stopshort = [0.0]

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
 
    def next(self):         
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
        fastrsi = self.rsi[0]

        #Signals
        up1 = True if self.trend[-1] == 1 and (self.data.low[0] < self.center2[-1] or self.p.usefastsma == False) and self.redbars[-1] == 1 else False 
        dn1 = True if self.trend[-1] == -1 and (self.data.high[0] > self.center2[-1] or self.p.usefastsma == False) and self.greenbars[-1] == 1 else False 
        up2 = True if self.data.high[0] < self.center[-1] and self.data.high[0] < self.center2[-1] and self.bar[-1] == -1 and self.p.needex == True else False 
        dn2 = True if self.data.low[0] > self.center[-1] and self.data.low[0] > self.center2[-1] and self.bar[-1] == 1 and self.p.needex == True else False 
        up3 = 1 if self.data.close[0] < self.data.open[0] and self.len[0] > self.sma[0] * 3 and self.minV[0] < self.minV[-1] and fastrsi < 10 else 0

        self.printdebuginfonextinner()

        #Trading
        if up1 == 1 and self.p.needstops == True:
            self.stoplong.append(self.data.close - (self.data.close / 100 * self.p.stoppercent))
        else: 
            self.stoplong.append(self.stoplong[-1])

        if dn1 == 1 and self.p.needstops == True:
            self.stopshort.append(self.data.close + (self.data.close / 100 * self.p.stoppercent))
        else: 
            self.stopshort.append(self.stopshort[-1])

        fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59,59)
        currdt = self.data.datetime.datetime()

        gmt3_tz = pytz.timezone('Etc/GMT-3')
        fromdt = pytz.utc.localize(fromdt)
        todt = pytz.utc.localize(todt)
        currdt = gmt3_tz.localize(currdt, is_dst=True)

        if (up1 or up2 or up3) and currdt > fromdt and currdt < todt:
            if self.curr_position < 0:
                if args.debug:
                    self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                if args.debug:
                    self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))

            if self.p.needlong and self.curr_position == 0:
                if args.debug:
                    self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.buy(size=10, tradeid=self.curtradeid)
                self.curr_position = 1
                if args.debug:
                    self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))

        if dn1 and currdt > fromdt and currdt < todt:
            if self.curr_position > 0:
                if args.debug:
                    self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                if args.debug:
                    self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))

            if self.p.needshort and self.curr_position == 0:
                if args.debug:
                    self.log('!!! BEFORE OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.sell(size=10, tradeid=self.curtradeid)
                self.curr_position = -1
                if args.debug:
                    self.log('!!! AFTER OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, cerebro.broker.getcash()))

        if currdt > todt:
            self.close(tradeid=self.curtradeid)
            self.curr_position = 0

        self.printdebuginfonextend()

    def notify_order(self, order):
        if args.debug:
            self.log('notify_order() - Order status: %s' % order.Status[order.status])
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                if args.debug:
                    buytxt = 'BUY COMPLETE, {} - at {}'.format(order.executed.price, bt.num2date(order.executed.dt))
                    self.log(buytxt)
            else:
                if args.debug:
                    selltxt = 'SELL COMPLETE, {} - at {}'.format(order.executed.price, bt.num2date(order.executed.dt))
                    self.log(selltxt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            pass  # Simply log

    def notify_trade(self, trade):
        if args.debug:
            self.log('!!! notify_trade() - self.curr_position={}, traderef={}'.format(self.curr_position, trade.ref))
        if trade.isclosed:
            tradesclosed[trade.ref] = trade
            print('---------------------------- TRADE CLOSED --------------------------')
            print("1: Data Name:                            {}".format(trade.data._name))
            print("2: Bar Num:                              {}".format(len(trade.data)))
            print("3: Current date:                         {}".format(self.data.datetime.date()))
            print('4: Status:                               Trade Complete')
            print('5: Ref:                                  {}'.format(trade.ref))
            print('6: PnL:                                  {}'.format(round(trade.pnl,2)))
            self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))
            print('--------------------------------------------------------------------')

        elif trade.justopened:
            tradesopen[trade.ref]= trade
            if args.debug:
                self.log('TRADE JUST OPENED, SIZE {}, REF {}, CASH {}'.format(trade.size, trade.ref, cerebro.broker.getcash()))

    def stop(self):
        global batch_number
        batch_number += 1
        print('!! Finished Batch #: {},  params={}'.format(batch_number, vars(self.params)))

    def printdebuginfonextinner(self):
        if args.debug:
            self.log('----------------------')
            ddanalyzer = self.analyzers.dd.get_analysis()
            self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
            self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
            self.log('self.curr_position = {}'.format(self.curr_position))
            self.log('self.position = {}'.format(self.position))
            self.log('cerebro.broker.get_cash() = {}'.format(cerebro.broker.get_cash()))
            self.log('cerebro.broker.get_value() = {}'.format(cerebro.broker.get_value()))
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
            self.log('up1 = {} - True if self.trend[-1]({}) == 1 and (self.data.low[0]({}) < self.center2[-1]({}) or self.p.usefastsma({}) == False) and self.redbars[-1]({}) == 1 else False'.format(up1, self.trend[-1], self.data.low[0], self.center2[-1], self.p.usefastsma, self.redbars[-1]))
            self.log('dn1 = {} - True if self.trend[-1]({}) == -1 and (self.data.high[0]({}) > self.center2[-1]({}) or self.p.usefastsma({}) == False) and self.greenbars[-1]({}) == 1 else False'.format(dn1, self.trend[-1], self.data.high[0], self.center2[-1], self.p.usefastsma, self.greenbars[-1]))
            self.log('up2 = {} - True if self.data.high[0]({}) < self.center[-1]({}) and self.data.high[0]({}) < self.center2[-1]({}) and self.bar[-1]({}) == -1 and self.p.needex({}) == True else False'.format(up2, self.data.high[0], self.center[-1], self.data.high[0], self.center2[-1], self.bar[-1], self.p.needex))
            self.log('dn2 = {}'.format(dn2))
            self.log('up3 = {} - 1 if self.data.close[0]({}) < self.data.open[0]({}) and self.len[0]({}) > self.sma[0]({}) * 3 and self.minV[0]({}) < self.minV[-1]({}) and fastrsi({}) < 10 else 0'.format(up3, self.data.close[0], self.data.open[0], self.len[0], self.sma[0], self.minV[0], self.minV[-1], fastrsi))
            self.log('----------------------')

    def printdebuginfonextend(self):
        if args.debug:
            print('---------------------------- NEXT DEBUG ----------------------------')
            print("1: Data Name:                            {}".format(data._name))
            print("2: Bar Num:                              {}".format(len(data)))
            print("3: Current date:                         {}".format(data.datetime.datetime()))
            print('4: Open:                                 {}'.format(data.open[0]))
            print('5: High:                                 {}'.format(data.high[0]))
            print('6: Low:                                  {}'.format(data.low[0]))
            print('7: Close:                                {}'.format(data.close[0]))
            print('8: Volume:                               {}'.format(data.volume[0]))
            print('9: RSI:                                  {}'.format(self.rsi[0]))
            print('10: Current Position:                    {}'.format(self.curr_position))
            print('--------------------------------------------------------------------')

def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    #Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    #printDict(analyzer)
    netprofit = round(analyzer.pnl.netprofit.total, 8)
    grossprofit = round(analyzer.pnl.grossprofit.total, 8)
    grossloss = round(analyzer.pnl.grossloss.total, 8)
    profitfactor = round(analyzer.total.profitfactor, 3)
    strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2))
    buyandhold_return = round(analyzer.total.buyandholdreturn, 8)
    buyandhold_return_pct = round(analyzer.total.buyandholdreturnpct, 2)
    #Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Win Rate','Win Streak', 'Losing Streak', '']
    h3 = ['Buy & Hold Return', 'Buy & Hold Return, %', '', '']
    h4 = ['Net Profit','Gross Profit', 'Gross Loss', 'Profit Factor']
    r1 = [total_open, total_closed,total_won,total_lost]
    r2 = [strike_rate, win_streak, lose_streak, '']
    r3 = [buyandhold_return, buyandhold_return_pct, '', '']
    r4 = [netprofit, grossprofit, grossloss, profitfactor]

    #Print the rows
    print_list = [h1,r1,h2,r2, h3, r3, h4, r4]
    row_format ="{:<25}" * (len(h1) + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('',*row))

def printSQN(analyzer):
    sqn = round(analyzer.sqn,2)
    print('SQN: {}'.format(sqn))

def printDrawDown(analyzer):
    print('Max Drawdown: {}'.format(round(analyzer.max.moneydown, 2)))
    print('Max Drawdown, %: {}%'.format(round(analyzer.max.drawdown, 2)))
    print('Max Drawdown Length: {}'.format(round(analyzer.max.len, 2)))

def printDict(dict):
    for keys,values in dict.items():
        print(keys)
        print(values)

args = parse_args()

#Variable for our starting cash
startcash = 100000
 
# Create an instance of cerebro
cerebro = bt.Cerebro(optreturn=False, optdatas=True)

#Add our strategy
cerebro.optstrategy(BatchAlexNoroTrendMAsStrategy,
    needlong=(False, True),
    needshort=(False, True),
    needstops=False,
    stoppercent=5,
    usefastsma=(False, True),
    fastlen=range(3, 6),
    slowlen=21, #range(10, 41),
    bars=range(0, 6),
    needex=(False, True),
    fromyear=1900,
    toyear=2100,
    frommonth=1,
    tomonth=12,
    fromday=1,
    today=31)

data = btfeeds.GenericCSVData(
    dataname='bitfinex-BTCUSDT-15m.csv',
    buffered=True,
    #fromdate=datetime(2018, 10, 1),
    #todate=datetime(2118, 12, 31),
    timeframe=TimeFrame.Ticks,
    #compression=15,
    dtformat="%Y-%m-%dT%H:%M:%S",
    #nullvalue=0.0,
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=5,
    openinterest=-1
)
 
#Add the data to Cerebro
cerebro.adddata(data)

# Set our desired cash start
cerebro.broker.setcash(startcash)

# Add the analyzers we are interested in
cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd")
cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=cerebro.broker.getcash())

#add the sizer
if args.commsizer:
    cerebro.addsizer(maxRiskSizerComms, debug=args.debug, risk=args.risk)
else:
    cerebro.addsizer(maxRiskSizer, debug=args.debug, risk=args.risk)

if args.commtype.lower() == 'percentage':
    cerebro.broker.setcommission(args.commission)

# Run over everything
opt_runs = cerebro.run()

# Generate results list
final_results_list = []
for run in opt_runs:
    for strategy in run:
        value = round(strategy.broker.get_value(),2)
        PnL = round(value - startcash,2)
        period = strategy.params.period
        final_results_list.append([period,PnL])










# Run over everything
#strategies = cerebro.run()

#Get final portfolio Value
#portvalue = cerebro.broker.getvalue()
#pnl = portvalue - startcash
#pnlpct = 100 * (portvalue/startcash) - 100
 
#Print out the final result
#print('\n')
#for k, t in tradesclosed.items():
    #    opentrade = tradesopen[k]
    #side = 'Long' if opentrade.size > 0 else 'Short'
    #print('Trade Ref: {}'.format(t.ref))
    #print('Trade Price: {}'.format(t.price))
    #print('Trade Side: {}'.format(side))
    #print('Trade dtopen: {}'.format(bt.num2date(t.dtopen)))
    #print('Trade dtclose: {}'.format(bt.num2date(t.dtclose)))
    #print('Trade barlen: {}'.format(t.barlen))
    #print('Trade Profit NET: {}'.format(t.pnlcomm))
    #print('Trade Profit GROSS: {}\n'.format(t.pnl))

# print the analyzers
#firstStrat = strategies[0]
#printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
#printSQN(firstStrat.analyzers.sqn.get_analysis())
#printDrawDown(firstStrat.analyzers.dd.get_analysis())

#print('\nTotal # trades: {}'.format(len(tradesclosed.items())))

#print('Final Portfolio Value: {}'.format(round(portvalue, 2)))
#print('P/L: {}'.format(round(pnl, 2)))
#print('P/L, %: {}%'.format(round(pnlpct, 2)))

#Finally plot the end results
#cerebro.plot(style='candlestick')