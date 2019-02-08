'''
Step 2 of backtesting process
'''
 
import argparse
import os
import csv
import pandas as pd
from config.optimization import StrategyOptimizationFactory


class BacktestingStep2(object):

    _INDEX_NUMBERS_ARR = [0, 1, 2, 3, 4]

    _SORT_FINAL_RESULTS_COLUMN_NAME = "Net Profit"

    _params = None
    _input_filename = None
    _output_file1_full_name = None
    _ofile1 = None
    _writer1 = None
    _step2_model = None

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

    def read_csv_data(self, filename):
        return pd.read_csv(filename, index_col=self._INDEX_NUMBERS_ARR)

    def get_header_names(self, df):
        return list(df.index.names) + list(df.columns.values)

    def get_unique_index_values(self, df, name):
        return df.index.get_level_values(name).unique()

    def filter_top_records(self, df):
        filter = StrategyOptimizationFactory.create_filters()
        return filter.filter(df)

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename1(self, base_path, args):
        return '{}/{}_Step2.csv'.format(base_path, args.runid)

    def init_output_files(self, args):
        base_dir = self.whereAmI()
        output_path = self.get_output_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)

        self._output_file1_full_name = self.get_output_filename1(output_path, args)

        self._ofile1 = open(self._output_file1_full_name, "w")
        self._writer1 = csv.writer(self._ofile1, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    def printheader(self, writer, arr):
        # Print header
        print_list = [arr]
        for row in print_list:
            writer.writerow(row)

    def do_filter_input_data(self, df):
        final_results = []

        strat_list = self.get_unique_index_values(df, 'Strategy ID')
        exc_list = self.get_unique_index_values(df, 'Exchange')
        sym_list = self.get_unique_index_values(df, 'Currency Pair')
        tf_list = self.get_unique_index_values(df, 'Timeframe')

        for strategy in strat_list: # [strat_list[0]]:
            for exchange in exc_list:  # [exc_list[0]]:
                for symbol in sym_list:  # [sym_list[0]]:
                    for timeframe in tf_list:  # [tf_list[0]]:
                        idx = pd.IndexSlice
                        candidates_data_df = df.loc[idx[strategy, exchange, symbol, timeframe, :], idx[:]]
                        candidates_data_df = self.filter_top_records(candidates_data_df)
                        if candidates_data_df is not None and len(candidates_data_df) > 0:
                            print("Processing: {}/{}/{}/{}:\nNumber of best rows: {}\n".format(strategy, exchange, symbol, timeframe, len(candidates_data_df.values)))
                            candidates_data_df = candidates_data_df.reset_index()
                            final_results.extend(candidates_data_df.values.tolist())
                            #print("candidates_data_df.values={}\n".format(candidates_data_df.values))

        print("==========================\nFinal number of rows: {}".format(len(final_results)))
        return final_results

    def sort_results(self, arr, header_names):
        sort_by_column_idx = header_names.index(self._SORT_FINAL_RESULTS_COLUMN_NAME)
        return sorted(arr, key=lambda x: x[sort_by_column_idx], reverse=True)

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

        step1_df = self.read_csv_data(self._input_filename)

        header_names = self.get_header_names(step1_df)

        step1_df = step1_df.sort_index()

        self.init_output_files(args)

        self.printheader(self._writer1, header_names)

        final_results = self.do_filter_input_data(step1_df)

        print("Writing Step2 backtesting run results to: {}".format(self._output_file1_full_name))

        final_results = self.sort_results(final_results, header_names)

        self.printfinalresults(self._writer1, final_results)

        self.cleanup()


def main():
    step = BacktestingStep2()
    step.run()


if __name__ == '__main__':
    main()