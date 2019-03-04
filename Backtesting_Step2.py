'''
Step 2 of backtesting process
'''
 
import argparse
import os
import csv
import pandas as pd
from config.optimization import StrategyOptimizationFactory
from plotting.equity_curve import EquityCurvePlotter
from config.strategy_config import AppConfig


class BacktestingStep2(object):

    _ENABLE_FILTERING = AppConfig.is_global_step2_enable_filtering()

    _INDEX_NUMBERS_ARR = [0, 1, 2, 3, 4]

    def __init__(self):
        self._equity_curve_plotter = EquityCurvePlotter("Step2")
        self._params = None
        self._input_filename = None
        self._bktest_equity_curve_filename = None
        self._output_file1_full_name = None
        self._ofile1 = None
        self. _writer1 = None
        self._step2_model = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtesting Step 2')

        parser.add_argument('-r', '--runid',
                            type=str,
                            required=True,
                            help='Name of the output file(RunId****) from Step1')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step1.csv'.format(dirname, args.runid, args.runid)

    def get_bktest_equity_curve_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step1_EquityCurveData.csv'.format(dirname, args.runid, args.runid)

    def read_csv_data(self, filename):
        return pd.read_csv(filename, index_col=self._INDEX_NUMBERS_ARR)

    def get_header_names(self, df):
        return list(df.index.names) + list(df.columns.values)

    def get_unique_index_values(self, df, name):
        return df.index.get_level_values(name).unique()

    def filter_top_records(self, df):
        filter = StrategyOptimizationFactory.get_filters_step2()
        return filter.filter(df)

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename(self, base_path, args):
        return '{}/{}_Step2.csv'.format(base_path, args.runid)

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

    def filter_input_data(self, df):
        column_names = self.get_all_column_names(df)
        final_results = []

        strat_list = self.get_unique_index_values(df, 'Strategy ID')
        exc_list = self.get_unique_index_values(df, 'Exchange')
        sym_list = self.get_unique_index_values(df, 'Currency Pair')
        tf_list = self.get_unique_index_values(df, 'Timeframe')

        for strategy in strat_list:
            for exchange in exc_list:
                for symbol in sym_list:
                    for timeframe in tf_list:
                        idx = pd.IndexSlice
                        candidates_data_df = df.loc[idx[strategy, exchange, symbol, timeframe, :], idx[:]]
                        if self._ENABLE_FILTERING is True:
                            candidates_data_df = self.filter_top_records(candidates_data_df)
                        if candidates_data_df is not None and len(candidates_data_df) > 0:
                            print("Processing: {}/{}/{}/{}:\nNumber of best rows: {}\n".format(strategy, exchange, symbol, timeframe, len(candidates_data_df.values)))
                            candidates_data_df = candidates_data_df.reset_index()
                            final_results.extend(candidates_data_df.values.tolist())
                            #print("candidates_data_df.values={}\n".format(candidates_data_df.values))

        print("==========================\nFinal number of rows: {}".format(len(final_results)))
        return pd.DataFrame(final_results, columns=column_names)

    def sort_results(self, df):
        df_sorted = df.sort_values(by=["Strategy ID", "Exchange", "Currency Pair", "Timeframe"])

        return df_sorted

    def printfinalresults(self, writer, df):
        arr = df.values
        print_list = []
        print_list.extend(arr)
        print("Writing {} rows...".format(len(print_list)))
        for item in print_list:
            writer.writerow(item)
        self._ofile1.flush()

    def cleanup(self):
        self._ofile1.close()

    def run(self):
        args = self.parse_args()

        self._input_filename = self.get_input_filename(args)

        step1_df = self.read_csv_data(self._input_filename)

        header_names = self.get_header_names(step1_df)

        step1_df = step1_df.sort_index()

        self.init_output_files(args)

        self.printheader(self._writer1, header_names)

        step2_results_df = self.filter_input_data(step1_df)

        print("Writing Step 2 backtesting run results to: {}".format(self._output_file1_full_name))

        step2_results_df = self.sort_results(step2_results_df)

        self.printfinalresults(self._writer1, step2_results_df)

        self._bktest_equity_curve_filename = self.get_bktest_equity_curve_input_filename(args)

        bktest_equity_curve_df = self.read_csv_data(self._bktest_equity_curve_filename)

        self._equity_curve_plotter.generate_images(step2_results_df, bktest_equity_curve_df, args)

        self.cleanup()


def main():
    step = BacktestingStep2()
    step.run()


if __name__ == '__main__':
    main()