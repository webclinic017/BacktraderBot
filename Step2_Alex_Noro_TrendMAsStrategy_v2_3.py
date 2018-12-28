'''
Step2: Prepare analytics on Step1 results of backtesting of strategy: Alex(Noro) Trend MAs v2.3
'''
 
import argparse
import os
import csv
import pandas as pd
import ast

batch_number = 0
header_dateranges_months = {}
final_results = {}

ofile = None
csv_writer = None

def parse_args():
    parser = argparse.ArgumentParser(description='Alex(Noro) Trend MAs v2.3 Strategy')

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
    return '{}/strategyrun_results/TrendMAs2_3/{}/{}/{}_Step1.csv'.format(dirname, args.exchange, args.runid, args.runid)

def get_cumulative_pnl(data_dict):
    initial_pnl = 100.0
    pnl = initial_pnl
    for key, stats_dict in data_dict.items():
        monthly_pnl_pct = float(stats_dict["_monthly_pnl"])
        pnl = pnl * (1 + monthly_pnl_pct/100.00)

    return round((pnl - initial_pnl)*100/initial_pnl, 2)

def get_pct_losing_months(data_dict):
    result = 0.0
    for key, stats_dict in data_dict.items():
        monthly_pnl_pct = float(stats_dict["_monthly_pnl"])
        if(monthly_pnl_pct < 0):
            result = result + 1
    return 100 * result/len(data_dict)

def calculate_stats(data):
    result = data.copy()
    for index, row in data.items():
        if("_TotalStats" not in row):
            result[index]["_TotalStats"] = {}
        total_stats_dict = result[index]["_TotalStats"]
        total_stats_dict["Cumulative Pnl"] = get_cumulative_pnl(row["_MonthlyStats"])
        total_stats_dict["Pct Losing Months"] = get_pct_losing_months(row["_MonthlyStats"])

    return result

def printheader():
    #Designate the rows
    h1 = ['Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'Cumulative Pnl, %', 'Losing Months, %']
    for k, v in header_dateranges_months.items():
        h1.append(k)

    #Print header
    print_list = [h1]
    for row in print_list:
        csv_writer.writerow(row)

def printfinalresults(results):
    print_list = []

    for index, final_row in results.items():
        print_row = []
        print_row.append(final_row["Exchange"])
        print_row.append(final_row["Currency Pair"])
        print_row.append(final_row["Timeframe"])
        print_row.append(final_row["Parameters"])
        print_row.append(final_row["_TotalStats"]["Cumulative Pnl"])
        print_row.append("{}%".format(final_row["_TotalStats"]["Pct Losing Months"]))
        monthly_stats_dict = final_row["_MonthlyStats"]
        for k, month_data in monthly_stats_dict.items():
            print_row.append(month_data["_MonthlyReportValue"])
        print_list.append(print_row)

    for row in print_list:
        csv_writer.writerow(row)

def init_output():
    dirname = whereAmI()
    output_path = '{}/strategyrun_results/TrendMAs2_3/{}/{}'.format(dirname, args.exchange, args.runid)
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
    monthly_report_str = "{}% | {}% | {}".format(data["Net Profit, %"], data["Max Drawdown, %"], data["Total Closed Trades"])
    return {"_monthly_pnl": data["Net Profit, %"], "_MonthlyReportValue": monthly_report_str}

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

final_results = calculate_stats(final_results)

printheader()
print("!!! len(final_results)={}".format(len(final_results)))
printfinalresults(final_results)

ofile.close()   

