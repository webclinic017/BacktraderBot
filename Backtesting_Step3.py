'''
Step 3 of backtesting process
'''
 
import backtrader as bt
import backtrader.feeds as btfeeds

import argparse
from backtrader import TimeFrame
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from common.stfetcher import StFetcher
from strategies.config import BTStrategyConfig
from strategies.strategy import BTStrategyEnum
from datetime import datetime
from datetime import timedelta
from datetime import date
import os
import csv
import pandas as pd
import ast
from backtrader.sizers import FixedSize
import gc

month_num_days = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

final_results = []
step3_results = {}

batch_number = 0
step3_dateranges_months = {}

ofile = None
csv_writer = None


def parse_args():
    parser = argparse.ArgumentParser(description='Backtesting Step 3')

    parser.add_argument('-y', '--strategy',
                        type=str,
                        required=True,
                        help='The strategy ID')

    parser.add_argument('-d', '--testdaterange',
                        type=str,
                        required=True,
                        help='Step3 testing date range in the following format (startdate-enddate): \"YYYYMMDD-YYYYMMDD\"')

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
                        default=0.0015,
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
    strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(args.strategy)
    path_prefix = strategy_enum.value.prefix_name
    return '{}/strategyrun_results/{}/{}/{}/{}_Step2.csv'.format(dirname, path_prefix, args.exchange, args.runid, args.runid)


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


def init_output():
    dirname = whereAmI()
    strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(args.strategy)
    path_prefix = strategy_enum.value.prefix_name
    output_path = '{}/strategyrun_results/{}/{}/{}'.format(dirname, path_prefix, args.exchange, args.runid)
    os.makedirs(output_path, exist_ok=True)
    output_file_full_name = '{}/{}_Step3.csv'.format(output_path, args.runid)
    print("Writing Step3 optimization results to: {}".format(output_file_full_name))

    global ofile
    ofile = open(output_file_full_name, "w")
    #sys.stdout = ofile
    global csv_writer
    csv_writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)


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


def get_step1_key(exc, curr, tf, params):
    return "{}-{}-{}-{}".format(exc, curr, tf, params)


def get_processing_daterange(data):
    result = {}

    range_splitted = data.split('-')
    start_date = range_splitted[0]
    end_date = range_splitted[1]
    s = datetime.strptime(start_date, '%Y%m%d') 
    e = datetime.strptime(end_date, '%Y%m%d') 

    result['fromyear'] = s.year
    result['frommonth'] = s.month
    result['fromday'] = s.day
    result['toyear'] = e.year
    result['tomonth'] = e.month
    result['today'] = e.day
    return result


def get_processing_daterange_str2(fromyear, frommonth, fromday, toyear, tomonth, today):
    return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(fromyear, frommonth, fromday, toyear, tomonth, today)


def get_processing_months(proc_daterange):
    result = {}

    fromyear  = int(proc_daterange['fromyear'])
    frommonth = int(proc_daterange['frommonth'])
    fromday   = int(proc_daterange['fromday'])
    toyear    = int(proc_daterange['toyear'])
    tomonth   = int(proc_daterange['tomonth'])
    today     = int(proc_daterange['today'])
    fromdate_month = date(fromyear, frommonth, 1)
    todate_month   = date(toyear, tomonth, 1)
    for curryear in range(fromyear, toyear + 1):
        for currmonth in range(1, 13):
            currdate_month = date(curryear, currmonth, 1)
            if (currdate_month >= fromdate_month and currdate_month <= todate_month):
                daterange_str = get_processing_daterange_str2(curryear, currmonth, 1, curryear, currmonth, get_month_num_days(currmonth))
                result[daterange_str] = ""

    return result


def get_parameters_map(parameters_json):
    return ast.literal_eval(parameters_json)


def get_month_num_days(month):
    return month_num_days[month]


def add_strategy(strategy_enum, parameters_map, year, month):
    strategy_class = strategy_enum.value.clazz
    step3_params = BTStrategyConfig.get_step3_strategy_params(strategy_enum).copy()
    step3_params.update(parameters_map)
    step3_params.update({("debug", args.debug),
                         ("fromyear", year),
                         ("toyear", year),
                         ("frommonth", month),
                         ("tomonth", month),
                         ("fromday", 1),
                         ("today", get_month_num_days(month))})
    StFetcher.register(strategy_class, **step3_params)


def add_strategies_for_each_month(strategy_enum, parameters_map, proc_daterange):
    result = 0
    fromyear  = int(proc_daterange['fromyear'])
    frommonth = int(proc_daterange['frommonth'])
    fromday   = int(proc_daterange['fromday'])
    toyear    = int(proc_daterange['toyear'])
    tomonth   = int(proc_daterange['tomonth'])
    today     = int(proc_daterange['today'])
    fromdate_month = date(fromyear, frommonth, 1)
    todate_month   = date(toyear, tomonth, 1)
    #print("add_strategies_for_each_month(): fromdate_month={}, todate_month={}".format(fromdate_month, todate_month))
    for curryear in range(fromyear, toyear + 1):
        for currmonth in range(1, 13):
            currdate_month = date(curryear, currmonth, 1)
            if (currdate_month >= fromdate_month and currdate_month <= todate_month):
                #print("To process: currdate_month={}, fromdate_month={}, todate_month={}, get_month_num_days={}".format(currdate_month, fromdate_month, todate_month, get_month_num_days(currmonth)))
                add_strategy(strategy_enum, parameters_map, curryear, currmonth)
                result = result + 1

    return result


def getparametersstr(params):
    coll = vars(params).copy()
    del coll["debug"]
    del coll["fromyear"]
    del coll["toyear"]
    del coll["frommonth"]
    del coll["tomonth"]
    del coll["fromday"]
    del coll["today"]
    return "{}".format(coll)


def get_monthly_stats(net_profit_pct, max_drawdown, strike_rate, total_closed):
    monthly_report_str = "{:05.2f}% | {:04.2f}% | {} | {}".format(net_profit_pct, max_drawdown, strike_rate, total_closed)
    return {"_monthly_pnl": net_profit_pct, "_maxdd_pct": max_drawdown, "_MonthlyReportValue": monthly_report_str}


def get_cumulative_pnl(data_dict):
    initial_pnl = 10.0
    pnl = initial_pnl
    for key, stats_dict in data_dict.items():
        monthly_pnl_pct = float(stats_dict["_monthly_pnl"])
        pnl = pnl * (1 + monthly_pnl_pct/100.00)

    return round((pnl - initial_pnl)*100/initial_pnl, 2)


def get_average_pnl(data_dict):
    sum_pnl = 0.0
    for key, stats_dict in data_dict.items():
        monthly_pnl_pct = float(stats_dict["_monthly_pnl"])
        sum_pnl = sum_pnl + monthly_pnl_pct

    return round(sum_pnl/len(data_dict), 2)

def get_worst_maxdd_across_all_months(data_dict):
    result = 0
    for key, stats_dict in data_dict.items():
        maxdd_pct = float(stats_dict["_maxdd_pct"])
        if(maxdd_pct < result):
            result = maxdd_pct
    return result


def get_average_maxdd_across_all_months(data_dict):
    sum_maxdd = 0.0
    for key, stats_dict in data_dict.items():
        sum_maxdd = sum_maxdd + float(stats_dict["_maxdd_pct"])

    return round(sum_maxdd/len(data_dict), 2)


def get_pct_winning_months(data_dict):
    result = 0.0
    for key, stats_dict in data_dict.items():
        monthly_pnl_pct = float(stats_dict["_monthly_pnl"])
        if(monthly_pnl_pct >= 0):
            result = result + 1
    return round(100 * result/len(data_dict), 2)


def get_total_rank(avg_pnl, avg_max_dd_pct, pct_winning_months):
    avg_pnl_f = float(avg_pnl) if(float(avg_pnl) > 1.0) else 1.0 
    avg_max_dd_f = float(avg_max_dd_pct)
    pct_winning_months_f = float(pct_winning_months)

    total_rank = int(10000 * round(avg_pnl_f) + 100 * round(100 - abs(avg_max_dd_f)) + round(pct_winning_months_f))

    return total_rank


def add_total_stats_for_row(row_arr, monthly_stats_dict):
    cumulative_pnl = get_cumulative_pnl(monthly_stats_dict)
    avg_pnl = get_average_pnl(monthly_stats_dict)
    worst_max_dd_pct = get_worst_maxdd_across_all_months(monthly_stats_dict)
    avg_max_dd_pct = get_average_maxdd_across_all_months(monthly_stats_dict)
    pct_winning_months = get_pct_winning_months(monthly_stats_dict)
    total_rank = get_total_rank(avg_pnl, avg_max_dd_pct, pct_winning_months)

    row_arr.append(cumulative_pnl)
    row_arr.append(avg_pnl)
    row_arr.append(worst_max_dd_pct)
    row_arr.append(avg_max_dd_pct)
    row_arr.append("{}".format(pct_winning_months))
    row_arr.append("{}".format(total_rank))

    return row_arr


def printheader(step2_df):
    #Designate the rows
    step3_data_header = sorted(step3_dateranges_months.keys())
    h1 = step2_df.columns.tolist()
    h1.extend(['Step3: Cumulative Pnl, %', 'Step3: Avg Pnl, %', 'Step3: Worst Max DD, %', 'Step3: Avg Max DD, %', 'Step3: Winning Months, %', 'Step3: Total Rank'])

    for k in step3_data_header:
        h1.append("Step3: {}".format(k))

    #Print header
    print_list = [h1]
    for row in print_list:
        csv_writer.writerow(row)


def printfinalresults(results):
    print_list = []
    print_list.extend(results)

    for row in print_list:
        csv_writer.writerow(row)


args = parse_args()

startcash = 100000

filepath = get_input_filename()

step2_df = pd.read_csv(filepath, index_col=[0, 1, 2])
step2_df = step2_df.sort_index()
exc_list = step2_df.index.get_level_values('Exchange').unique()
sym_list = step2_df.index.get_level_values('Currency Pair').unique()
tf_list = step2_df.index.get_level_values('Timeframe').unique()

init_output()

strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(args.strategy)

for exchange in exc_list: #[exc_list[0]]:
    for symbol in sym_list: #[sym_list[0]]:
        for timeframe in tf_list:  #[tf_list[0]]:
            candidates_data_df = step2_df.loc[(exchange, symbol, timeframe)]
            # Get list of candidates from Step2 for exchange/symbol/timeframe/date range
            test_date_range = args.testdaterange
            proc_daterange = get_processing_daterange(test_date_range)
            proc_months = get_processing_months(proc_daterange)
            print("\n******** Processing {} rows for: {}, {}, {}, {} ********".format(len(candidates_data_df), exchange, symbol, timeframe, test_date_range))
        
            cerebro = init_cerebro(startcash)

            marketdata_filename = get_marketdata_filename(exchange, symbol, timeframe)
            marketdata = get_marketdata(marketdata_filename, proc_daterange)
            cerebro.adddata(marketdata)

            c = 1
            for index, data_row in candidates_data_df.iterrows():
                step1_key = get_step1_key(index[0], index[1], index[2], data_row["Parameters"])
                if(not step1_key in step3_results):
                    step3_results[step1_key] = {}
                parameters_map = get_parameters_map(data_row['Parameters'])
                stratnum = add_strategies_for_each_month(strategy_enum, parameters_map, proc_daterange)
                #print("Added {} strategies for processing".format(stratnum))
                #c = c + 1
                #if (c > 1):
                #    break

            cerebro.optstrategy(StFetcher, idx=StFetcher.COUNT())

            # clock the start of the process
            tstart = datetime.now()
            tstart_str = tstart.strftime("%Y-%m-%d %H:%M:%S")

            print("!! Started current run at {}. Number of strategies={}".format(tstart_str, len(StFetcher.COUNT())))
            # Run over everything
            stratruns = cerebro.run()

            # clock the end of the process
            tend = datetime.now()
            tend_str = tend.strftime("%Y-%m-%d %H:%M:%S")

            print("Cerebro has processed {} strategies at {}".format(len(stratruns), tend_str))

            # Clean up and destroy cerebro
            cerebro.runstop()
            cerebro = None
            StFetcher.cleanall()
            gc.collect()

            # Generate results list
            for run in stratruns:
                strategy = run[0]
                ta_analysis  = strategy.analyzers.ta.get_analysis()
                sqn_analysis = strategy.analyzers.sqn.get_analysis()
                dd_analysis  = strategy.analyzers.dd.get_analysis()
                total_closed = ta_analysis.total.closed if exists(ta_analysis, ['total', 'closed']) else 0
                #net_profit = round(ta_analysis.pnl.netprofit.total, 8) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total/startcash, 2) if exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                total_won = ta_analysis.won.total if exists(ta_analysis, ['won', 'total']) else 0
                strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
                max_drawdown = round(dd_analysis.max.drawdown, 2)
                max_drawdown_length = round(dd_analysis.max.len, 2)
                #profitfactor = round(ta_analysis.total.profitfactor, 3) if exists(ta_analysis, ['total', 'profitfactor']) else 0
                #buyandhold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if exists(ta_analysis, ['total', 'buyandholdreturnpct']) else 0
                daterange = strategy.getdaterange()

                step1_key = get_step1_key(exchange, symbol, timeframe, getparametersstr(strategy.params))
                if (step1_key not in step3_results):
                    step3_results[step1_key] = {}

                result_row = step3_results[step1_key]
                if ("_MonthlyStats" not in result_row):
                    result_row["_MonthlyStats"] = {}
                monthly_stats_dict = result_row["_MonthlyStats"]
                daterange = strategy.getdaterange()
                step3_dateranges_months[daterange] = ""
                monthly_stats_dict[daterange] = get_monthly_stats(net_profit_pct, max_drawdown, strike_rate, total_closed)

step3_header_names = sorted(step3_dateranges_months.keys())
step3_dateranges_months = {}
for ii in step3_header_names:
    step3_dateranges_months[ii] = ""
step2_df = step2_df.reset_index()
printheader(step2_df)

# Get Step2 results list and merge Step3 results into it
final_results_copy = step2_df.values.tolist()
final_results = []

print("len(step3_results)={}".format(len(step3_results)))
for final_row in final_results_copy:
    step1_key = get_step1_key(final_row[0], final_row[1], final_row[2], final_row[3])
    if(step1_key in step3_results):
        added_row = final_row
        step3_results_dict = step3_results[step1_key]
        monthly_stats_dict = step3_results_dict["_MonthlyStats"]
        added_row = add_total_stats_for_row(added_row, monthly_stats_dict)
        if(len(monthly_stats_dict) > 0):
            for key_month, month in step3_dateranges_months.items():
                if (key_month in monthly_stats_dict.keys()):
                   added_row.append(monthly_stats_dict[key_month]["_MonthlyReportValue"])
                else:
                   added_row.append(" ")
            final_results.append(added_row)


printfinalresults(final_results)

ofile.close()