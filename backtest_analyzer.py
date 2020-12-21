'''
Backtesting results analyzer
'''

import argparse
import os
import csv
import pandas as pd
from model.reports_common import ColumnName
import re
from model.common import BacktestRunKey
from model.common import BacktestAnalyzerData
from model.common import EquityCurveData
from model.common import MonteCarloData
from model.common import BktestAnalyzerGroupingData
from model.bktestanalyzermodel import BktestAnalyzerModel

DEFAULT_PARAMS_REGEX = "('exitmode'.*)"


class BacktestAnalyzer(object):
    _INDEX_NUMBERS_SHORT_ARR = [0, 1, 2, 3]
    _INDEX_NUMBERS_ALL_ARR = [ColumnName.STRATEGY_ID, ColumnName.EXCHANGE, ColumnName.CURRENCY_PAIR, ColumnName.TIMEFRAME, ColumnName.PARAMETERS]

    _params = None
    _input_filename = None
    _output_file1_full_name = None
    _ofile1 = None
    _writer1 = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtest Analyzer')

        parser.add_argument('-r', '--runid', type=str, required=True, help='Run Id (Run****)')
        parser.add_argument('-f', '--filename', type=str, required=True, help='Name of output CSV file')

        parser.add_argument('--debug', action='store_true', help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}'.format(dirname, args.runid, args.filename)

    def read_csv_data(self, filename):
        return pd.read_csv(filename, index_col=self._INDEX_NUMBERS_SHORT_ARR)

    def get_header_names(self, df):
        return list(df.index.names) + list(df.columns.values)

    def get_unique_index_values(self, df, name):
        return df.index.get_level_values(name).unique()

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename(self, base_path, args):
        return '{}/{}_Analysis.csv'.format(base_path, args.runid)

    def init_output_files(self, args):
        base_dir = self.whereAmI()
        output_path = self.get_output_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)

        self._output_file1_full_name = self.get_output_filename(output_path, args)

        self._ofile1 = open(self._output_file1_full_name, "w")
        self._writer1 = csv.writer(self._ofile1, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    def printheader(self, writer, arr):
        # Print header
        print_list = [arr]
        for row in print_list:
            writer.writerow(row)

    def backup_parameters(self, input_df):
        input_df['Parameters Original'] = input_df[ColumnName.PARAMETERS]
        return input_df

    def is_params_grouping_enabled(self):
        paramsregex = DEFAULT_PARAMS_REGEX
        return paramsregex is not None and paramsregex != ""

    def handle_parameters(self, input_df):
        result_df = input_df

        paramsregex = DEFAULT_PARAMS_REGEX
        if self.is_params_grouping_enabled():
            df_copy = input_df.copy()
            i = 0
            for index, row in input_df.iterrows():
                parameters_str = row[ColumnName.PARAMETERS]
                params_match_obj = re.search(paramsregex, parameters_str)
                if params_match_obj:
                    param_group_key = params_match_obj.group(1)
                    df_copy.iloc[i, 0] = param_group_key
                i += 1

            df_copy = df_copy.reset_index(drop=False)
            result_df = df_copy.set_index(self._INDEX_NUMBERS_ALL_ARR)

        return result_df

    def get_pct_val(self, val):
        return "{}%".format(round(val, 2))

    def calc_average(self, arr):
        len_non_zero = len(list(filter(lambda x: (x != 0), arr)))
        return sum(arr) / float(len_non_zero) if len_non_zero != 0 else 0

    def get_field_value(self, df, field_name):
        try:
            result = df[field_name]
        except KeyError:
            result = ""
        return result

    def create_model(self, df):
        model = BktestAnalyzerModel()

        #pd.set_option('display.max_columns', None)  # or 1000
        #pd.set_option('display.max_rows', None)  # or 1000
        #pd.set_option('display.max_colwidth', -1)  # or 199
        # print("group_fwtest_sorted_df={}".format(group_fwtest_sorted_df.to_string()))

        c = 0
        unique_groups_df = df.index.unique()
        for group_idx in unique_groups_df:
            c += 1
            print("Processing {}/{} group ...".format(c, len(unique_groups_df)))
            group_df = df.loc[group_idx]
            group_bktest_sorted_df = group_df.sort_values(by=[ColumnName.NET_PROFIT], ascending=False)
            group_bktest_best_row_df = group_bktest_sorted_df.iloc[0]
            group_bktest_rows_count = len(group_bktest_sorted_df[ColumnName.NET_PROFIT_PCT])
            group_bktest_avg_net_profict_pct = group_bktest_sorted_df[ColumnName.NET_PROFIT_PCT].mean()
            group_bktest_profitable_count = len(group_bktest_sorted_df[group_bktest_sorted_df[ColumnName.NET_PROFIT_PCT] > 0])
            group_bktest_profitable_count_pct = 100 * group_bktest_profitable_count / group_bktest_rows_count

            run_key = BacktestRunKey()
            run_key.strategyid = group_idx[0]
            run_key.exchange = group_idx[1]
            run_key.currency_pair = group_idx[2]
            run_key.timeframe = group_idx[3]

            bktestanalyzergrouping_data = BktestAnalyzerGroupingData()
            bktestanalyzergrouping_data.parameters_grouping_key = group_idx[4] if self.is_params_grouping_enabled() else "N/A"
            bktestanalyzergrouping_data.parameters_best_record_in_group = group_bktest_best_row_df["Parameters Original"]

            analyzer_data = BacktestAnalyzerData()
            analyzer_data.total_closed_trades = self.get_field_value(group_bktest_best_row_df, ColumnName.TOTAL_CLOSED_TRADES)
            analyzer_data.sl_trades_count = self.get_field_value(group_bktest_best_row_df, ColumnName.TRADES_NUM_SL_COUNT)
            analyzer_data.tsl_trades_count = self.get_field_value(group_bktest_best_row_df, ColumnName.TRADES_NUM_TSL_COUNT)
            analyzer_data.tp_trades_count = self.get_field_value(group_bktest_best_row_df, ColumnName.TRADES_NUM_TP_COUNT)
            analyzer_data.ttp_trades_count = self.get_field_value(group_bktest_best_row_df, ColumnName.TRADES_NUM_TTP_COUNT)
            analyzer_data.tb_trades_count = self.get_field_value(group_bktest_best_row_df, ColumnName.TRADES_NUM_TB_COUNT)
            analyzer_data.dca_triggered_count = self.get_field_value(group_bktest_best_row_df, ColumnName.TRADES_NUM_DCA_TRIGGERED_COUNT)
            analyzer_data.net_profit_pct = self.get_pct_val(group_bktest_best_row_df[ColumnName.NET_PROFIT_PCT])
            analyzer_data.max_drawdown_pct = self.get_pct_val(group_bktest_best_row_df[ColumnName.MAX_DRAWDOWN_PCT])
            analyzer_data.max_drawdown_length = group_bktest_best_row_df[ColumnName.MAX_DRAWDOWN_LENGTH]
            analyzer_data.net_profit_to_maxdd = group_bktest_best_row_df[ColumnName.NET_PROFIT_TO_MAX_DRAWDOWN]
            analyzer_data.win_rate_pct = group_bktest_best_row_df[ColumnName.WIN_RATE_PCT]
            analyzer_data.profit_factor = group_bktest_best_row_df[ColumnName.PROFIT_FACTOR]

            equity_curve_data = EquityCurveData()
            equity_curve_data.equitycurvervalue = group_bktest_best_row_df[ColumnName.EQUITY_CURVE_R_VALUE]
            equity_curve_data.equitycurversquaredvalue = group_bktest_best_row_df[ColumnName.EQUITY_CURVE_R_SQUARED_VALUE]

            montecarlo_data = MonteCarloData()
            montecarlo_data.mc_riskofruin_pct = group_bktest_best_row_df[ColumnName.MC_RISK_OF_RUIN_PCT]

            bktestanalyzergrouping_data.total_rows = group_bktest_rows_count
            bktestanalyzergrouping_data.avg_net_profit_pct = self.get_pct_val(group_bktest_avg_net_profict_pct)
            bktestanalyzergrouping_data.bktest_profitable_records_num = group_bktest_profitable_count
            bktestanalyzergrouping_data.bktest_profitable_records_pct = self.get_pct_val(group_bktest_profitable_count_pct)

            model.add_result_row(run_key, analyzer_data, equity_curve_data, montecarlo_data, bktestanalyzergrouping_data)

        return model

    def printfinalresults(self, writer, arr):
        print_list = []
        print_list.extend(arr)
        for item in print_list:
            writer.writerow(item)

    def cleanup(self):
        self._ofile1.close()

    def run(self):
        args = self.parse_args()

        self._input_filename = self.get_input_filename(args)

        input_df = self.read_csv_data(self._input_filename)

        input_df = self.backup_parameters(input_df)

        input_df = self.handle_parameters(input_df)

        input_df = input_df.sort_index()

        self.init_output_files(args)

        model = self.create_model(input_df)

        print("Writing backtesting analysis results into: {}".format(self._output_file1_full_name))

        self.printheader(self._writer1, model.get_header_names())

        self.printfinalresults(self._writer1, model.get_model_data_arr())

        self.cleanup()


def main():
    step = BacktestAnalyzer()
    step.run()


if __name__ == '__main__':
    main()
