'''
Step 5 of backtesting process
'''
 
import argparse
import os
import csv
import pandas as pd
from config.optimization import StrategyOptimizationFactory
from plotting.equity_curve import EquityCurvePlotter
from model.step5model import Step5Model
import re

class BacktestingStep5(object):

    _ENABLE_FILTERING = True

    _INDEX_NUMBERS_ARR = [0, 1, 2, 3, 4]

    _equity_curve_plotter = EquityCurvePlotter("Step5")
    _params = None
    _input_filename = None
    _fwtest_equity_curve_filename = None
    _output_file1_full_name = None
    _ofile1 = None
    _writer1 = None
    _step5_model = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtesting Step 5')

        parser.add_argument('-r', '--runid',
                            type=str,
                            required=True,
                            help='Name of the output file(RunId****) from Step4')

        parser.add_argument('--commission',
                            default=0.0015,
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step4.csv'.format(dirname, args.runid, args.runid)

    def get_bktest_equity_curve_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step1_EquityCurveData.csv'.format(dirname, args.runid, args.runid)

    def get_fwtest_equity_curve_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step3_EquityCurveData.csv'.format(dirname, args.runid, args.runid)

    def read_csv_data(self, filename):
        return pd.read_csv(filename, index_col=self._INDEX_NUMBERS_ARR)

    def find_rows_for_strategy(self, df, strategy):
        try:
            idx = pd.IndexSlice
            result = df.loc[idx[strategy, :], idx[:]]
        except KeyError:
            result = None
        return result

    def filter_top_records(self, df):
        filter = StrategyOptimizationFactory.get_filters_step5()
        return filter.filter(df)

    def get_top_values_per_strategy(self, df):
        result = []
        all_strategies = self.get_unique_index_values(df, 'Strategy ID')
        for strategy in all_strategies:
            strategy_rows_df = self.find_rows_for_strategy(df, strategy)
            if strategy_rows_df is not None:
                filtered_rows = self.filter_top_records(strategy_rows_df)
                result.append(filtered_rows)
        return pd.concat(result)

    def parse_monthly_stats(self, df, columns):
        result = {}
        for column in columns:
            daterange_regex = "(\d{8}-\d{8})"
            month_range = re.search(daterange_regex, column)
            if month_range:
                month_value = df[column]
                net_profit_pct = re.match("[-+]?[0-9]*\.?[0-9]+", month_value)
                if net_profit_pct:
                    net_profit_pct = float(net_profit_pct.group())
                    month_key = month_range.group(1)
                    result[month_key] = net_profit_pct
        return result

    def parse_pct_to_float(self, str_val):
        val = str_val.replace("%", "")
        return float(val)

    def parse_dataframe_to_model(self, df, args):
        model = Step5Model()
        df = df.copy()
        df = df.reset_index()
        for index, row in df.iterrows():
            strategyid          = row['Strategy ID']
            exchange            = row['Exchange']
            currency_pair       = row['Currency Pair']
            timeframe           = row['Timeframe']
            parameters          = row['Parameters']
            commission          = args.commission * 100
            leverage            = 1
            pyramiding          = 1
            profit_factor       = row['Profit Factor']
            win_rate_pct        = self.parse_pct_to_float(row['Win Rate, %'])
            max_drawdown_pct    = row['Max Drawdown, %']
            total_closed_trades = row['Total Closed Trades']
            monthly_stats = self.parse_monthly_stats(row, df.columns.values)
            model.add_result_column(strategyid, exchange, currency_pair, timeframe, parameters, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats)
        return model

    def get_daterange(self, df):
        result = None
        if len(df) > 0:
            result = df.head(1)["Date Range"].values[0]
        return result

    def get_header_names(self, df):
        return list(df.index.names) + list(df.columns.values)

    def get_unique_index_values(self, df, name):
        return df.index.get_level_values(name).unique()

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename(self, base_path, args):
        return '{}/{}_Step5.csv'.format(base_path, args.runid)

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

    def get_all_column_names(self, df):
        result = []
        df_copy = df.copy()
        df_copy = df_copy.reset_index()
        result.extend(list(df_copy.columns.values))
        return result

    def sort_results(self, df):
        df_sorted = df.sort_values(by=["Strategy ID", "Exchange", "Currency Pair", "Timeframe"])

        return df_sorted

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

        step4_df = self.read_csv_data(self._input_filename)

        top_values_df = self.get_top_values_per_strategy(step4_df)

        self._step5_model = self.parse_dataframe_to_model(top_values_df, args)

        self.init_output_files(args)

        print("Writing Step 5 backtesting run results to: {}".format(self._output_file1_full_name))

        self.printfinalresults(self._writer1, self._step5_model.get_model_data_arr())

        bktest_equity_curve_df = self.read_csv_data(self.get_bktest_equity_curve_filename(args))
        fwtest_equity_curve_df = self.read_csv_data(self.get_fwtest_equity_curve_filename(args))
        self._equity_curve_plotter.generate_combined_top_results_images_step5(top_values_df, bktest_equity_curve_df, fwtest_equity_curve_df, args)

        self.cleanup()


def main():
    step = BacktestingStep5()
    step.run()


if __name__ == '__main__':
    main()