'''
Step 2 of backtesting process
'''
 
import argparse
import os
import csv
import pandas as pd
import ast
from strategies.strategy import BTStrategyEnum

batch_number = 0
header_dateranges_months = {}
final_results = {}

ofile = None
csv_writer = None

def parse_args():
    parser = argparse.ArgumentParser(description='Backtesting Step 2')

    parser.add_argument('-y', '--strategy',
                        type=str,
                        required=True,
                        help='The strategy ID')

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

def get_input_filename():
    dirname = whereAmI()
    strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(args.strategy)
    path_prefix = strategy_enum.value.prefix_name
    return '{}/strategyrun_results/{}/{}/{}/{}_Step1.csv'.format(dirname, path_prefix, args.exchange, args.runid, args.runid)


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

def add_total_stats(data):
    result = data.copy()
    for index, row in data.items():
        if("_TotalStats" not in row):
            result[index]["_TotalStats"] = {}
        total_stats_dict = result[index]["_TotalStats"]
        total_stats_dict["Cumulative Pnl"] = get_cumulative_pnl(row["_MonthlyStats"])
        total_stats_dict["Avg Pnl"] = get_average_pnl(row["_MonthlyStats"])
        total_stats_dict["Worst Max DD Pct"] = get_worst_maxdd_across_all_months(row["_MonthlyStats"])
        total_stats_dict["Avg Max DD Pct"] = get_average_maxdd_across_all_months(row["_MonthlyStats"])
        total_stats_dict["Pct Winning Months"] = get_pct_winning_months(row["_MonthlyStats"])
        total_stats_dict["Total Rank"] = get_total_rank(total_stats_dict["Avg Pnl"], total_stats_dict["Avg Max DD Pct"], total_stats_dict["Pct Winning Months"])

    return result


def printheader():
    #Designate the rows
    h1 = ['Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'Step2: Cumulative Pnl, %', 'Step2: Avg Pnl, %', 'Step2: Worst Max DD, %', 'Step2: Avg Max DD, %', 'Step2: Winning Months, %', 'Step2: Total Rank']
    for k, v in header_dateranges_months.items():
        h1.append("Step2: {}".format(k))

    #Print header
    print_list = [h1]
    for row in print_list:
        csv_writer.writerow(row)

def printfinalresults(results):
    print_list = []

    for item in results:
        final_row = item[1]
        print_row = []
        print_row.append(final_row["Exchange"])
        print_row.append(final_row["Currency Pair"])
        print_row.append(final_row["Timeframe"])
        print_row.append(final_row["Parameters"])
        print_row.append(final_row["_TotalStats"]["Cumulative Pnl"])
        print_row.append(final_row["_TotalStats"]["Avg Pnl"])
        print_row.append(final_row["_TotalStats"]["Worst Max DD Pct"])
        print_row.append(final_row["_TotalStats"]["Avg Max DD Pct"])
        print_row.append("{}".format(final_row["_TotalStats"]["Pct Winning Months"]))
        print_row.append("{}".format(final_row["_TotalStats"]["Total Rank"]))
        monthly_stats_dict = final_row["_MonthlyStats"]
        for key_h in header_dateranges_months.keys():
            if(key_h in monthly_stats_dict):
                print_row.append(monthly_stats_dict[key_h]["_MonthlyReportValue"])
            else:
                print_row.append(" ")
        print_list.append(print_row)

    for row in print_list:
        csv_writer.writerow(row)

def init_output():
    dirname = whereAmI()
    strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(args.strategy)
    path_prefix = strategy_enum.value.prefix_name
    output_path = '{}/strategyrun_results/{}/{}/{}'.format(dirname, path_prefix, args.exchange, args.runid)
    os.makedirs(output_path, exist_ok=True)
    output_file_full_name = '{}/{}_Step2.csv'.format(output_path, args.runid)
    print("Writing Step2 results to: {}".format(output_file_full_name))

    global ofile
    ofile = open(output_file_full_name, "w")
    #sys.stdout = ofile
    global csv_writer
    csv_writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

def get_step1_key(exc, curr, tf, params):
    return "{}-{}-{}-{}".format(exc, curr, tf, params)

def get_monthly_stats(data):
    win_rate_str = data["Win Rate, %"].replace("%", "")
    monthly_report_str = "{:05.2f}% | {:04.2f}% | {} | {}".format(data["Net Profit, %"], data["Max Drawdown, %"], data["Win Rate, %"], data["Total Closed Trades"])
    return {"_monthly_pnl": data["Net Profit, %"], "_maxdd_pct": data["Max Drawdown, %"], "_MonthlyReportValue": monthly_report_str}

def strip_unnecessary_params(parameters_json):
    coll = ast.literal_eval(parameters_json)
    del coll["fromyear"]
    del coll["toyear"]
    del coll["frommonth"]
    del coll["tomonth"]
    del coll["fromday"]
    del coll["today"]
    return "{}".format(coll) 

args = parse_args()

filepath = get_input_filename()

step1_list_df = pd.read_csv(filepath)
print("!!! len(step1_list_df)={}".format(len(step1_list_df)))

init_output()

for index, step1_row in step1_list_df.iterrows():
    parameters_str = strip_unnecessary_params(step1_row["Parameters"])
    step1_key = get_step1_key(step1_row["Exchange"], step1_row["Currency Pair"], step1_row["Timeframe"], parameters_str)
    if(step1_key not in final_results):
        final_results[step1_key] = {}

    result_row = final_results[step1_key]
    result_row["Exchange"] = step1_row["Exchange"]
    result_row["Currency Pair"] = step1_row["Currency Pair"]
    result_row["Timeframe"] = step1_row["Timeframe"]
    result_row["Parameters"] = parameters_str

    if("_MonthlyStats" not in result_row):
        result_row["_MonthlyStats"] = {}
    monthly_stats_dict = result_row["_MonthlyStats"]
    daterange = step1_row["Date Range"]
    header_dateranges_months[daterange] = ""
    monthly_stats_dict[daterange] = get_monthly_stats(step1_row)

final_results = add_total_stats(final_results)

#Sort Results List
final_results = sorted(final_results.items(), key=lambda kv: kv[1]["_TotalStats"]["Total Rank"], reverse=True)

printheader()
print("!!! len(final_results)={}".format(len(final_results)))
printfinalresults(final_results)

ofile.close()   

