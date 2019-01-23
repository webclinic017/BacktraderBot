'''
Step 1 of backtesting process
'''
 
import backtrader as bt
import backtrader.feeds as btfeeds

import argparse
from backtrader import TimeFrame
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from datetime import datetime
from datetime import timedelta
from strategies.config import BTStrategyConfig
from strategies.strategy import BTStrategyEnum
import time
import sys
import os
import csv
from backtrader.sizers import FixedSize
import pandas as pd

batch_number = 0

def parse_args():
    parser = argparse.ArgumentParser(description='Backtesting Step 1')

    parser.add_argument('-y', '--strategy',
                        type=str,
                        required=True,
                        help='The strategy ID')

    parser.add_argument('-e', '--exchange',
                        type=str,
                        required=True,
                        help='The exchange name')

    parser.add_argument('-s', '--symbol',
                        type=str,
                        required=True,
                        help='The Symbol/Currency Pair To Process')

    parser.add_argument('-t', '--timeframe',
                        type=str,
                        required=True,
                        help='The timeframe')

    parser.add_argument('-x', '--maxcpus',
                        type=int,
                        default=8,
                        choices=[1, 2, 3, 4, 5, 7, 8],
                        help='The max number of CPUs to use for processing')

    parser.add_argument('-r', '--runid',
                        type=str,
                        default="",
                        required=True,
                        help='Run ID')

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
                        default=0.0015,
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

 
def check_csv_has_data_for_datarange(filename):
    df = pd.read_csv(filename)
    startdate = datetime(args.fromyear, args.frommonth, args.fromday, 0, 0, 0)
    enddate = datetime(args.toyear, args.tomonth, args.today, 0, 0, 0)
    for index, row in df.iterrows():
        timestamp_str = row['Timestamp']
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
        if(startdate < timestamp and enddate < timestamp):
            return False
        else:
            return True

def exists(obj, chain):
    _key = chain.pop(0)
    if _key in obj:
        return exists(obj[_key], chain) if chain else obj[_key]


def getdaterange():
    return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(args.fromyear, args.frommonth, args.fromday, args.toyear, args.tomonth, args.today)


def getlotsize():
    return "Lot{}{}".format(args.lotsize, "Pct" if args.lottype == "Percentage" else "Unit")


def getparametersstr(params):
    coll = vars(params).copy()
    del coll["debug"]     
    return "{}".format(coll)


def printfinalresultsheader(csv_writer):
    #Designate the rows
    h1 = ['Exchange', 'Currency Pair', 'Timeframe', 'Date Range', 'Lot Size', 'Total Closed Trades', 'Net Profit', 'Net Profit, %', 'Max Drawdown, %', 'Max Drawdown Length', 'Win Rate, %', 'Profit Factor', 'Buy & Hold Return, %', 'Parameters']

    #Print header
    print_list = [h1]
    for row in print_list:
        csv_writer.writerow(row)

def printfinalresults(csv_writer, results):
    #section_size = 40

    #if(len(results) < 2 * section_size):
    #    print_list = []
    #    print_list.extend(results) 
    #    for row in print_list:
    #        if(is_positive_profit(row)):
    #            csv_writer.writerow(row)
    #else:
    #    print_list1 = []
    #    print_list1.extend(results[0:section_size])
    #    for row1 in print_list1:
    #        if(is_positive_profit(row1) == True):
    #            csv_writer.writerow(row1)

    print_list = []
    print_list.extend(results) 
    for row in print_list:
        csv_writer.writerow(row)


def is_positive_profit(data_row):
    return data_row[7] > 0

def optimization_step(strat):
    global batch_number
    batch_number += 1
    st = strat[0]
    st.strat_id = batch_number
    print('!! Finished Batch Run={}'.format(batch_number))

args = parse_args()


def whereAmI():
    return os.path.dirname(os.path.realpath(__import__("__main__").__file__))


#Variable for our starting cash
startcash = 100000
  
# Create an instance of cerebro
cerebro = bt.Cerebro(optreturn=True, maxcpus=args.maxcpus)

cerebro.optcallback(optimization_step)

#Add our strategy
strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(args.strategy)
strategy_class = strategy_enum.value.clazz
step1_params = BTStrategyConfig.get_step1_strategy_params(strategy_enum).copy()
step1_params.update({   ("debug", args.debug),
                        ("fromyear", args.fromyear),
                        ("toyear", args.toyear),
                        ("frommonth", args.frommonth),
                        ("tomonth", args.tomonth),
                        ("fromday", args.fromday),
                        ("today", args.today)})

cerebro.optstrategy(strategy_class, **step1_params)

input_file_full_name = './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(args.exchange, args.symbol, args.timeframe, args.exchange, args.symbol, args.timeframe)
if(not check_csv_has_data_for_datarange(input_file_full_name)):
    print("!!! There is no market data for the start/end date range provided. Finishing execution.")
    quit()

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
path_prefix = strategy_enum.value.prefix_name
output_path = '{}/strategyrun_results/{}/{}/{}'.format(dirname, path_prefix, args.exchange, args.runid)
os.makedirs(output_path, exist_ok=True)
output_file_full_name = '{}/{}_Step1.csv'.format(output_path, args.runid)
print("Writing Step1 backtesting run results to: {}".format(output_file_full_name))

outputfile_exists = os.path.exists(output_file_full_name)
ofile = open(output_file_full_name, "a")
#sys.stdout = ofile
writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
if (outputfile_exists == False):
    printfinalresultsheader(writer)

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

        strat_key = strategy.strat_id
        total_closed = ta_analysis.total.closed if exists(ta_analysis, ['total', 'closed']) else 0
        net_profit = round(ta_analysis.pnl.netprofit.total, 8) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
        net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total/startcash, 2) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
        total_won = ta_analysis.won.total if exists(ta_analysis, ['won', 'total']) else 0
        strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
        max_drawdown = round(dd_analysis.max.drawdown, 2)
        max_drawdown_length = round(dd_analysis.max.len, 2)
        profitfactor = round(ta_analysis.total.profitfactor, 3) if exists(ta_analysis, ['total', 'profitfactor']) else 0
        buyandhold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if exists(ta_analysis, ['total', 'buyandholdreturnpct']) else 0
        parameters = getparametersstr(strategy.params)
        if(net_profit != 0 and total_closed > 0):
            final_results.append([args.exchange, args.symbol, args.timeframe, getdaterange(), getlotsize(), total_closed, net_profit, net_profit_pct, max_drawdown, max_drawdown_length, strike_rate, profitfactor, buyandhold_return_pct, parameters])

#Sort Results List
sorted_list = sorted(final_results, key=lambda x: (x[7], x[8]), reverse=True)

printfinalresults(writer, sorted_list)
ofile.close()