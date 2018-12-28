'''
Step2: Prepare analytics on Step1 results of backtesting of strategy: Alex(Noro) Trend MAs v2.3
'''
 
import argparse
import os
import csv
import pandas as pd
import ast

month_num_days = {1 : 31, 2 : 28, 3 : 31, 4 : 30, 5 : 31, 6 : 30, 7 : 31, 8 : 31, 9 : 30, 10 : 31, 11 : 30, 12 : 31}

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


def printheader():
    #Designate the rows
    h1 = ['Exchange', 'Currency Pair', 'Timeframe', 'Parameters']
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
        date_ranges_stats_dict = final_row["_DateRangesStats"]
        print_row.extend(date_ranges_stats_dict.values())
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

def get_daterange_stats_str(data):
    return "{}% | {}% | {}".format(data["Net Profit, %"], data["Max Drawdown, %"], data["Total Closed Trades"])

def strip_unnecessary_params(parameters_json):
    coll = ast.literal_eval(parameters_json)
    del coll["fromyear"]
    del coll["toyear"]
    del coll["frommonth"]
    del coll["tomonth"]
    del coll["fromday"]
    del coll["today"]
    return "{}".format(coll) 

def get_month_num_days(month):
    return month_num_days[month]

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
    if("_DateRangesStats" not in result_row):
        result_row["_DateRangesStats"] = {}

    date_ranges_stats_dict = result_row["_DateRangesStats"]
    daterange = step1_row["Date Range"]
    header_dateranges_months[daterange] = ""
    date_ranges_stats_dict[daterange] = get_daterange_stats_str(step1_row)

printheader()
print("!!! len(final_results)={}".format(len(final_results)))
printfinalresults(final_results)

ofile.close()   

