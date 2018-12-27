'''
Step2: Batch testing of the implementation of the TradingView strategy: Alex(Noro) Trend MAs v2.3
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
from datetime import date
import time
import sys
import os
import csv
import pandas as pd
import ast
from backtrader.sizers import PercentSizer
from backtrader.sizers import FixedSize

month_num_days = {1 : 31, 2 : 28, 3 : 31, 4 : 30, 5 : 31, 6 : 30, 7 : 31, 8 : 31, 9 : 30, 10 : 31, 11 : 30, 12 : 31}

batch_number = 0

ofile = None
csv_writer = None

class StFetcher(object):
    _STRATS = []

    @classmethod
    def register(cls, target, *args, **kwargs):
        cls._STRATS.append([target, args, kwargs])

    @classmethod
    def COUNT(cls):
        return range(len(cls._STRATS))

    def __new__(cls, *args, **kwargs):
        idx = kwargs.pop('idx')
        args_arr = cls._STRATS[idx][1]
        #args_arr = cerebro.datas + list(args_arr)  # Workaround on workaround, horrible!
        kwargs_arr = cls._STRATS[idx][2]
        obj = cls._STRATS[idx][0](*args, **kwargs_arr)
        return obj

def parse_args():
    parser = argparse.ArgumentParser(description='Alex(Noro) Trend MAs v2.3 Strategy')

    parser.add_argument('-x', '--maxcpus',
                        type=int,
                        default=8,
                        choices=[1, 2, 3, 4, 5, 7, 8],
                        help='The max number of CPUs to use for processing')

    parser.add_argument('-l', '--lottype',
                        type=str,
                        default="Percentage",
                        required=True,
                        choices=["Percentage", "Fixed"],
                        help='Lot type')

    parser.add_argument('--commtype',
                        default="Percentage",
                        type=str,
                        choices=["Percentage", "Fixed"],
                        help='The type of commission to apply to a trade')
 
    parser.add_argument('--commission',
                        default=0.001,
                        type=float,
                        help='The amount of commission to apply to a trade')

    parser.add_argument('-e', '--exchange',
                        type=str,
                        required=True,
                        help='The exchange name')

    parser.add_argument('-r', '--runid',
                        type=str,
                        required=True,
                        help='Name of the output file(RunId****) from Step1')
 
    parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Debugs'))
 
    return parser.parse_args()

def exists(obj, chain):
    _key = chain.pop(0)
    if _key in obj:
        return exists(obj[_key], chain) if chain else obj[_key]

def whereAmI():
    return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

def optimization_step(strat):
    global batch_number
    batch_number += 1
    st = strat[0]
    st.strat_id = batch_number
    print('!! Finished Batch Run={}'.format(batch_number))

def get_input_filename():
    dirname = whereAmI()
    return '{}/strategyrun_results/TrendMAs2_3/{}/{}/{}_Step1.csv'.format(dirname, args.exchange, args.runid, args.runid)

def init_cerebro(startcash):
    # Create an instance of cerebro
    cerebro = bt.Cerebro(optreturn=False, maxcpus=args.maxcpus)
    cerebro.optcallback(optimization_step)
    cerebro.broker.setcash(startcash)

    # Add the analyzers we are interested in
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd", initial_cash=startcash)
    cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=startcash)

    #add the sizer
    if(args.lottype != "" and args.lottype == "Percentage"):
        cerebro.addsizer(VariablePercentSizer, percents=98, debug=args.debug)
    else:
        cerebro.addsizer(FixedSize, stake=1)

    if args.commtype.lower() == 'percentage':
        cerebro.broker.setcommission(args.commission)

    return cerebro


def printheader():
    #Designate the rows
    h1 = ['Exchange', 'Currency Pair', 'Timeframe', 'Date Range', 'Parameters', 'Step2 Results (variable)...']

    #Print header
    print_list = [h1]
    for row in print_list:
        csv_writer.writerow(row)

def printfinalresults(results):
    print_list = []
    print_list.extend(results)
    for row in print_list:
        csv_writer.writerow(row)

def init_output():
    dirname = whereAmI()
    output_path = '{}/strategyrun_results/TrendMAs2_3/{}/{}'.format(dirname, args.exchange, args.runid)
    os.makedirs(output_path, exist_ok=True)
    output_file_full_name = '{}/{}_Step2.csv'.format(output_path, args.runid)
    print("Writing Step2 optimization results to: {}".format(output_file_full_name))

    global ofile
    ofile = open(output_file_full_name, "w")
    #sys.stdout = ofile
    global csv_writer
    csv_writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    printheader()

def get_marketdata_filename(exchange, symbol, timeframe):
    return './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(exchange, symbol, timeframe, exchange, symbol, timeframe)

def get_marketdata(filename, daterange):
    # Adjust from date to add more candle data from the past to strategy to prevent any calculation problems with indicators 
    fromdate_back_delta = timedelta(days=50) 
    fromdate_back = datetime(daterange['fromyear'], daterange['frommonth'], daterange['fromday']) - fromdate_back_delta
    # Adjust to date to add more candle data    
    todate_delta = timedelta(days=2)  
    todate_beyond = datetime(daterange['toyear'], daterange['tomonth'], daterange['today']) + todate_delta
    data = btfeeds.GenericCSVData(
        dataname=filename,
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
    return data
    
def get_step1_key(exc, curr, tf, daterange, params):
    return "{}-{}-{}-{}-{}".format(exc, curr, tf, daterange, params)

def get_processing_daterange(data):
    result = {}
    
    start_date=data[0].split('-')[0]
    end_date=data[-1].split('-')[1]
    s = datetime.strptime(start_date, '%Y%m%d') 
    e = datetime.strptime(end_date, '%Y%m%d') 

    result['fromyear'] = s.year
    result['frommonth'] = s.month
    result['fromday'] = s.day
    result['toyear'] = e.year
    result['tomonth'] = e.month
    result['today'] = e.day
    return result

def get_processing_daterange_str(proc_daterange):
    return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(proc_daterange['fromyear'], proc_daterange['frommonth'], proc_daterange['fromday'], proc_daterange['toyear'], proc_daterange['tomonth'], proc_daterange['today'])

def get_parameters_map(parameters_json):
    return ast.literal_eval(parameters_json)

def get_month_num_days(month):
    return month_num_days[month]

def add_strategy(parameters_map, year, month, step1_hk):
    StFetcher.register(AlexNoroTrendMAsStrategy, 
        debug=args.debug,
        needlong=parameters_map["needlong"],
        needshort=parameters_map["needshort"],
        needstops=parameters_map["needstops"],
        stoppercent=parameters_map["stoppercent"],
        usefastsma=parameters_map["usefastsma"],
        fastlen=parameters_map["fastlen"],
        slowlen=parameters_map["slowlen"],
        bars=parameters_map["bars"],
        needex=parameters_map["needex"],
        fromyear=year,
        toyear=year,
        frommonth=month,
        tomonth=month,
        fromday=1,
        today=get_month_num_days(month),
        step1_key=step1_hk
    )

def add_strategies_for_each_month(cerebro, parameters_map, proc_daterange, step1_key):
    result = 0
    fromyear  = int(proc_daterange['fromyear'])
    frommonth = int(proc_daterange['frommonth'])
    fromday   = int(proc_daterange['fromday'])
    toyear    = int(proc_daterange['toyear'])
    tomonth   = int(proc_daterange['tomonth'])
    today     = int(proc_daterange['today'])
    fromdate_month = date(fromyear, frommonth, 1)
    todate_month   = date(toyear, tomonth, 1)
    print("add_strategies_for_each_month(): fromdate_month={}, todate_month={}".format(fromdate_month, todate_month))
    for curryear in range(fromyear, toyear + 1):
        for currmonth in range(1, 13):
            currdate_month = date(curryear, currmonth, 1)
            if (currdate_month >= fromdate_month and currdate_month <= todate_month):
                #print("To process: currdate_month={}, fromdate_month={}, todate_month={}, get_month_num_days={}".format(currdate_month, fromdate_month, todate_month, get_month_num_days(currmonth)))
                add_strategy(parameters_map, curryear, currmonth, step1_key)
                result = result + 1

    return result

def getparametersstr(params):
    coll = vars(params)
    del coll["debug"]
    del coll["fromyear"]
    del coll["toyear"]
    del coll["frommonth"]
    del coll["tomonth"]
    del coll["fromday"]
    del coll["today"]
    del coll["step1_key"]       
    return "{}".format(coll)

final_results = []
step2_results = {}
args = parse_args()

startcash = 100000

filepath = get_input_filename()

#pd.set_option('display.max_colwidth', -1)
df = pd.read_csv(filepath, index_col=[0, 1, 2])
#df = df.sort_index()
exc_list = df.index.get_level_values('Exchange').unique()
sym_list = df.index.get_level_values('Currency Pair').unique()
tf_list = df.index.get_level_values('Timeframe').unique()

init_output()

for exchange in exc_list:
    for symbol in sym_list:
        for timeframe in tf_list:
            candidates_data_df = df.loc[(exchange, symbol, timeframe)]
            # Get list of candidates from Step1 for exchange/symbol/timeframe/date range
            date_range_candidates = df.loc[(exchange, symbol, timeframe), 'Date Range']
            proc_daterange = get_processing_daterange(date_range_candidates)
            if(len(candidates_data_df) > 0):
                print("\n******** Processing {} rows for: {}, {}, {}, {} ********".format(len(candidates_data_df), exchange, symbol, timeframe, get_processing_daterange_str(proc_daterange)))
        
            cerebro = init_cerebro(startcash)

            marketdata_filename = get_marketdata_filename(exchange, symbol, timeframe)
            marketdata = get_marketdata(marketdata_filename, proc_daterange)
            cerebro.adddata(marketdata)

            c = 1
            for index, data_row in candidates_data_df.iterrows():
                step1_key = get_step1_key(index[0], index[1], index[2], data_row["Date Range"], data_row["Parameters"])
                if(not step1_key in step2_results):
                    step2_results[step1_key] = []
                final_results.append([index[0], index[1], index[2], data_row["Date Range"], data_row["Parameters"]])
                parameters_map = get_parameters_map(data_row['Parameters'])
                stratnum = add_strategies_for_each_month(cerebro, parameters_map, proc_daterange, step1_key)
                print("Added {} strategies for processing".format(stratnum))
                #c = c + 1
                #if (c > 10):
                #    break

            cerebro.optstrategy(StFetcher, idx=StFetcher.COUNT())
            #cerebro.optstrategy(AlexNoroTrendMAsStrategy, debug=args.debug, needlong=True, needshort=True, needstops=False, stoppercent=5, usefastsma=True, fastlen=5, slowlen=22, bars=range(0, 3), needex=False, fromyear=2018, toyear=2018, frommonth=1, tomonth=1, fromday=1, today=31, step1_key="TEST DFDFSDF")

            # clock the start of the process
            tstart = time.time()

            # Run over everything
            stratruns = cerebro.run()

            # clock the end of the process
            tend = time.time()
            duration = int(tend - tstart)
            print("Cerebro has processed {} strategies in {} seconds".format(len(stratruns), duration))

            # Generate results list
            for run in stratruns:
                strategy = run[0]
                # print the analyzers
                ta_analysis  = strategy.analyzers.ta.get_analysis()
                sqn_analysis = strategy.analyzers.sqn.get_analysis()
                dd_analysis  = strategy.analyzers.dd.get_analysis()

                total_closed = ta_analysis.total.closed if exists(ta_analysis, ['total', 'closed']) else 0
                #net_profit = round(ta_analysis.pnl.netprofit.total, 8) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total/startcash, 8) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                #total_won = ta_analysis.won.total if exists(ta_analysis, ['won', 'total']) else 0
                #strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
                max_drawdown = round(dd_analysis.max.drawdown, 2)
                max_drawdown_length = round(dd_analysis.max.len, 2)
                #profitfactor = round(ta_analysis.total.profitfactor, 3) if exists(ta_analysis, ['total', 'profitfactor']) else 0
                #buyandhold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if exists(ta_analysis, ['total', 'buyandholdreturnpct']) else 0
                daterange = strategy.getdaterange()
                key = strategy.p.step1_key
                step2_results[key].append("{}: {} | {}% | {}%".format(daterange, total_closed, net_profit_pct, max_drawdown))


# Merge Step2 results into final list
for final_row in final_results:
    step1_key = get_step1_key(final_row[0], final_row[1], final_row[2], final_row[3], final_row[4])
    final_row.extend(step2_results[step1_key]) 

printfinalresults(final_results)

ofile.close()
        

