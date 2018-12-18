'''
Batch testing of the implementation of the TradingView strategy: Alex(Noro) Trend MAs v2.3
'''
 
import backtrader as bt
import backtrader.feeds as btfeeds

import math
import argparse
from backtrader import TimeFrame
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from strategies.trendmas import AlexNoroTrendMAsStrategy
from datetime import datetime
from datetime import timedelta
import time
import sys
import os
from backtrader.sizers import PercentSizer
from backtrader.sizers import FixedSize

batch_number = 0

def parse_args():
    parser = argparse.ArgumentParser(description='Alex(Noro) Trend MAs v2.3 Strategy')

    parser.add_argument('-e', '--exchange',
                        type=str,
                        required=True,
                        help='The exchange name')

    parser.add_argument('-s', '--symbol',
                        type=str,
                        required=True,
                        help='The Symbol of the Instrument/Currency Pair To Process')

    parser.add_argument('-t', '--timeframe',
                        type=str,
                        required=True,
                        help='The timeframe')

    parser.add_argument('-x', '--maxcpus',
                        type=int,
                        default=8,
                        choices=[1, 2, 3, 4, 5, 7, 8],
                        help='The max number of CPUs to use for processing')

    parser.add_argument('-p', '--prefix',
                        type=str,
                        default="",
                        required=True,
                        help='Optional prefix for output file name')

    parser.add_argument('-l', '--lottype',
                        type=str,
                        default="Percentage",
                        required=True,
                        choices=["Percentage", "Fixed"],
                        help='Lot type')

    parser.add_argument('-z', '--lotsize',
                        type=int,
                        default=98,
                        required=True,
                        help='Lot size: either percentage or number of units - depending on lottype parameter')

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

    parser.add_argument('--fromyear',
                        type=int,
                        required=True,
                        help='Date Range: From Year')

    parser.add_argument('--toyear',
                        type=int,
                        required=True,
                        help='Date Range: To Year')

    parser.add_argument('--frommonth',
                        type=int,
                        required=True,
                        help='Date Range: From Month')

    parser.add_argument('--tomonth',
                        type=int,
                        required=True,
                        help='Date Range: To Month')

    parser.add_argument('--fromday',
                        type=int,
                        required=True,
                        help='Date Range: From Day')

    parser.add_argument('--today',
                        type=int,
                        required=True,
                        help='Date Range: To Day')
 
    parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Debugs'))
 
    return parser.parse_args()

 
def exists(obj, chain):
    _key = chain.pop(0)
    if _key in obj:
        return exists(obj[_key], chain) if chain else obj[_key]


def getdaterange():
    return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(args.fromyear, args.frommonth, args.fromday, args.toyear, args.tomonth, args.today)


def getlotsize():
    return "Lot{}{}".format(args.lotsize, "Pct" if args.lottype == "Percentage" else "Unit")

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


def printfinalresults(results):
    #Designate the rows
    h1 = ['Id', 'Total Closed Trades', 'Net Profit', 'Net Profit, %', 'Win Rate, %', 'Max Drawdown, %', 'Max Drawdown Length', 'Profit Factor', 'Buy & Hold Return, %', 'Parameters']
    row_format ="{:<22}" * (len(h1) + 1)

    #Print the rows
    section_size = 20
    print("RESULTS:")
    print("{} - {} - {} - {} - {}:".format(args.exchange.upper(), args.symbol.upper(), args.timeframe.upper(), getdaterange(), getlotsize()))

    if(len(results) < 2 * section_size):
        print_list = [h1]
        print_list.extend(results) 
        print("\n******************************************************************* Final Results: *************************************************************************************** ")
        for row in print_list:
            print(row_format.format('', *row))
    else:
        print_list1 = [h1]
        print_list2 = [h1]
        print_list1.extend(results[0:section_size])
        print_list2.extend(results[-section_size:])

        print("Best Results:")
        print("******************************************************************* Final Results: *************************************************************************************** ")
        for row1 in print_list1:
            print(row_format.format('', *row1))
        print("\nWorst Results:")
        for row2 in print_list2:
            print(row_format.format('', *row2))

def printDict(dict):
    for keys,values in dict.items():
        print(keys)
        print(values)

def optimization_step(strat):
    global batch_number
    batch_number += 1
    st = strat[0]
    st.strat_id = batch_number
    #print('!! Finished Batch Run={}'.format(batch_number))

args = parse_args()


def whereAmI():
    return os.path.dirname(os.path.realpath(__import__("__main__").__file__))


#Variable for our starting cash
startcash = 100000
 
# Create an instance of cerebro
cerebro = bt.Cerebro(optreturn=True, maxcpus=args.maxcpus)

cerebro.optcallback(optimization_step)

#Add our strategy
cerebro.optstrategy(AlexNoroTrendMAsStrategy,
    debug=args.debug,
    needlong=True,
    needshort=True,
    needstops=False,
    stoppercent=5,
    usefastsma=True,
    fastlen=3,
    slowlen=21,
    bars=0,
    needex=False,
    fromyear=args.fromyear,
    toyear=args.toyear,
    frommonth=args.frommonth,
    tomonth=args.tomonth,
    fromday=args.fromday,
    today=args.today)

input_file_full_name = './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(args.exchange, args.symbol, args.timeframe, args.exchange, args.symbol, args.timeframe)
fromdate_back_delta = timedelta(days=50) # Adjust from date to add more candle data from the past to strategy to prevent any calculation problems with indicators 
fromdate_back = datetime(args.fromyear, args.frommonth, args.fromday) - fromdate_back_delta
todate_delta = timedelta(days=2) # Adjust to date to add more candle data 
todate_beyond = datetime(args.toyear, args.tomonth, args.today) + todate_delta
data = btfeeds.GenericCSVData(
    dataname=input_file_full_name,
    buffered=True,
    fromdate=fromdate_back,
    todate=todate_beyond,
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

dirname = whereAmI()
now = datetime.now()
output_datetime_dirname = now.strftime("%Y%m%d_%H%M%S")
daterange_str = getdaterange()
lotsize_str = getlotsize()
output_path = '{}/strategyrun_results/TrendMAs2_3/{}/{}/{}/{}_{}_{}_{}'.format(dirname, args.exchange, args.symbol, args.timeframe, output_datetime_dirname, args.prefix, daterange_str, lotsize_str)
os.makedirs(output_path, exist_ok=True)
output_file_full_name = '{}/run-output-{}-{}-{}-{}-{}.txt'.format(output_path, args.exchange, args.symbol, args.timeframe, daterange_str, lotsize_str)
print("Writing backtesting run results to: {}".format(output_file_full_name))
sys.stdout = open(output_file_full_name, "w")

#Add the data to Cerebro
cerebro.adddata(data)

# Set our desired cash start
cerebro.broker.setcash(startcash)

# Add the analyzers we are interested in
cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd", initial_cash=cerebro.broker.getcash())
cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=cerebro.broker.getcash())

#add the sizer
if(args.lottype != "" and args.lottype == "Percentage"):
    cerebro.addsizer(VariablePercentSizer, percents=98, debug=args.debug)
else:
    cerebro.addsizer(FixedSize, stake=1)

if args.commtype.lower() == 'percentage':
    cerebro.broker.setcommission(args.commission)

# clock the start of the process
tstart = time.time()

# Run over everything
stratruns = cerebro.run()

# clock the end of the process
tend = time.time()

# Generate results list
final_results = []
for run in stratruns:
    for strategy in run:
        # print the analyzers
        ta_analysis = strategy.analyzers.ta.get_analysis()
        sqn_analysis = strategy.analyzers.sqn.get_analysis()
        dd_analysis = strategy.analyzers.dd.get_analysis()
        #printTradeAnalysis(ta_analysis)
        #printSQN(sqn_analysis)
        #printDrawDown(dd_analysis)

        strat_key = strategy.strat_id
        total_closed = ta_analysis.total.closed if exists(ta_analysis, ['total', 'closed']) else 0
        net_profit = round(ta_analysis.pnl.netprofit.total, 8) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
        net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total/startcash, 8) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
        total_won = ta_analysis.won.total if exists(ta_analysis, ['won', 'total']) else 0
        strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
        max_drawdown = round(dd_analysis.max.drawdown, 2)
        max_drawdown_length = round(dd_analysis.max.len, 2)
        profitfactor = round(ta_analysis.total.profitfactor, 3) if exists(ta_analysis, ['total', 'profitfactor']) else 0
        buyandhold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if exists(ta_analysis, ['total', 'buyandholdreturnpct']) else 0
        parameters = "{}".format(vars(strategy.params))
        parameters = parameters.replace("{", "")
        parameters = parameters.replace("}", "")
        #if(net_profit != 0 and total_closed > 0):
        final_results.append([strat_key, total_closed, net_profit, net_profit_pct, strike_rate, max_drawdown, max_drawdown_length, profitfactor, buyandhold_return_pct, parameters])

# print out the result
print('\nTime used, seconds:', round(tend - tstart, 4))
print('\nTotal number of backtesting runs: {}'.format(batch_number))

#Sort Results List
sorted_list = sorted(final_results, key=lambda x: (x[3], x[5]), reverse=True)

printfinalresults(sorted_list)