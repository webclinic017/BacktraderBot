'''
Implementation of the TradingView strategy: Alex (Noro) Robot BitMEX Fast RSI v1.0
'''
 
import backtrader as bt
import backtrader.feeds as btfeeds
from datetime import datetime
import argparse
from backtrader import TimeFrame
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from strategies.fastrsi import AlexNoroRobotBitMEXFastRSIStrategy

tradesopen = {}
tradesclosed = {}

def parse_args():
    parser = argparse.ArgumentParser(description='Alex (Noro) Robot BitMEX Fast RSI v1.0 Strategy')
 
    parser.add_argument('--commtype',
                        default="Percentage",
                        type=str,
                        choices=["Percentage", "Fixed"],
                        help='The type of commission to apply to a trade')
 
    parser.add_argument('--commission',
                        default=0.0015,
                        type=float,
                        help='The amount of commission to apply to a trade')
 
    parser.add_argument('--risk',
                        default=0.02,
                        type=float,
                        help='The percentage of available cash to risk on a trade')
 
    parser.add_argument('--debug',
                        action ='store_true',
                        help=('Print Debug logs'))
 
    return parser.parse_args()

 
def exists(obj, chain):
    _key = chain.pop(0)
    if _key in obj:
        return exists(obj[_key], chain) if chain else obj[_key]


def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    #Get the results we are interested in
    total_open = analyzer.total.open if exists(analyzer, ['total', 'open']) else 0
    total_closed = analyzer.total.closed if exists(analyzer, ['total', 'closed']) else 0
    total_won = analyzer.won.total if exists(analyzer, ['won', 'total']) else 0
    total_lost = analyzer.lost.total if exists(analyzer, ['lost', 'total']) else 0
    win_streak = analyzer.streak.won.longest if exists(analyzer, ['streak', 'won', 'longest']) else 0
    lose_streak = analyzer.streak.lost.longest if exists(analyzer, ['streak', 'lost', 'longest']) else 0

    netprofit = round(analyzer.pnl.netprofit.total, 8) if exists(analyzer, ['pnl', 'netprofit', 'total']) else 0
    grossprofit = round(analyzer.pnl.grossprofit.total, 8) if exists(analyzer, ['pnl', 'grossprofit', 'total']) else 0
    grossloss = round(analyzer.pnl.grossloss.total, 8) if exists(analyzer, ['pnl', 'grossloss', 'total']) else 0
    profitfactor = round(analyzer.total.profitfactor, 3) if exists(analyzer, ['total', 'profitfactor']) else 0
    strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
    buyandhold_return = round(analyzer.total.buyandholdreturn, 8) if exists(analyzer, ['total', 'buyandholdreturn']) else 0
    buyandhold_return_pct = round(analyzer.total.buyandholdreturnpct, 2) if exists(analyzer, ['total', 'buyandholdreturnpct']) else 0

    #Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Win Rate', 'Win Streak', 'Losing Streak', '']
    h3 = ['Buy & Hold Return', 'Buy & Hold Return, %', '', '']
    h4 = ['Net Profit', 'Gross Profit', 'Gross Loss', 'Profit Factor']
    r1 = [total_open, total_closed, total_won, total_lost]
    r2 = [strike_rate, win_streak, lose_streak, '']
    r3 = [buyandhold_return, buyandhold_return_pct, '', '']
    r4 = [netprofit, grossprofit, grossloss, profitfactor]

    #Print the rows
    print_list = [h1, r1, h2, r2, h3, r3, h4, r4]
    row_format ="{:<25}" * (len(h1) + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('', *row))

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
cerebro = bt.Cerebro()

#Add our strategy
cerebro.addstrategy(AlexNoroRobotBitMEXFastRSIStrategy,
                    debug=args.debug,
                    needlong=True,
                    needshort=True,
                    rsiperiod=7,
                    rsibars=1,
                    rsilong=30,
                    rsishort=70,
                    useocf=True,
                    useccf=True,
                    openbars=1,
                    closebars=1,
                    useobf=True,
                    usecbf=True,
                    openbody=20,
                    closebody=20,
                    fromyear=2018,
                    toyear=2018,
                    frommonth=10,
                    tomonth=10,
                    fromday=1,
                    today=31)

data = btfeeds.GenericCSVData(
    dataname='bitfinex-BTCUSDT-3h.csv',
    fromdate=datetime(2018, 9, 1),
    todate=datetime(2018, 11, 2),
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
cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd", initial_cash=cerebro.broker.getcash())
cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=cerebro.broker.getcash())

#add the sizer
cerebro.addsizer(VariablePercentSizer, percents=98, debug=args.debug)

if args.commtype.lower() == 'percentage':
    cerebro.broker.setcommission(args.commission)
 
# Run over everything
strategies = cerebro.run()
 
#Get final portfolio Value
portvalue = cerebro.broker.getvalue()
pnl = portvalue - startcash
pnlpct = 100 * (portvalue/startcash) - 100
 
#Print out the final result
print('\n')
for k, t in tradesclosed.items():
    opentrade = tradesopen[k]
    side = 'Long' if opentrade.size > 0 else 'Short'
    print('Trade Ref: {}'.format(t.ref))
    print('Trade Price: {}'.format(t.price))
    print('Trade Side: {}'.format(side))
    print('Trade dtopen: {}'.format(bt.num2date(t.dtopen)))
    print('Trade dtclose: {}'.format(bt.num2date(t.dtclose)))
    print('Trade barlen: {}'.format(t.barlen))
    print('Trade Profit NET: {}'.format(t.pnlcomm))
    print('Trade Profit GROSS: {}\n'.format(t.pnl))

# print the analyzers
firstStrat = strategies[0]
printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
printSQN(firstStrat.analyzers.sqn.get_analysis())
printDrawDown(firstStrat.analyzers.dd.get_analysis())

print('\nTotal # trades: {}'.format(len(tradesclosed.items())))

print('Final Portfolio Value: {}'.format(round(portvalue, 2)))
print('P/L: {}'.format(round(pnl, 2)))
print('P/L, %: {}%'.format(round(pnlpct, 2)))

#Finally plot the end results
#cerebro.plot(b)
#cerebro.plot(style='candlestick')
