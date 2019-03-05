'''
Step 5 of backtesting process
'''
 
import argparse
import os
import csv
import pandas as pd
from config.optimization import StrategyOptimizationFactory
from plotting.equity_curve import EquityCurvePlotter
from model.step5modelgenerator import Step5ModelGenerator
from config.strategy_config import AppConfig


class BacktestingStep5(object):

    _ENABLE_FILTERING = AppConfig.is_global_step5_enable_filtering()

    _INDEX_NUMBERS_ARR = [0, 1, 2, 3, 4]

    def __init__(self):
        self._equity_curve_plotter = EquityCurvePlotter("Step5")
        self._params = None
        self._input_filename = None
        self._fwtest_equity_curve_filename = None
        self. _output_file1_full_name = None
        self._ofile1 = None
        self._writer1 = None
        self._step5_model = None

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

    def filter_top_records(self, df):
        filter = StrategyOptimizationFactory.get_filters_step5()
        return filter.filter(df)

    def get_value_index(self, arr, val):
        try:
            result = arr.index(val)
        except ValueError:
            result = None
        return result

    def get_top_rows_per_strategy(self, df):
        result = []
        selected_strategies_arr = []
        selected_currencypairs_arr = []
        df_copy = df.copy().reset_index(drop=False).sort_values(by='FwTest: Combined Net Profit', ascending=False)
        for index, row in df_copy.iterrows():
            strategy = row["Strategy ID"]
            currency_pair = row["Currency Pair"]
            if self.get_value_index(selected_strategies_arr, strategy) is None and self.get_value_index(selected_currencypairs_arr, currency_pair) is None:
                selected_strategies_arr.append(strategy)
                selected_currencypairs_arr.append(currency_pair)
                result.append(row)
        result_pd = pd.DataFrame(result)
        result_pd = result_pd.sort_values(by='Strategy ID', ascending=True)
        return result_pd

    def create_model(self, df, args):
        generator = Step5ModelGenerator()
        model = generator.generate_model(df, args)
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

        top_rows_df = self.filter_top_records(step4_df)

        self._step5_model = self.create_model(top_rows_df, args)

        self.init_output_files(args)

        print("Writing Step 5 backtesting run results to: {}".format(self._output_file1_full_name))

        self.printfinalresults(self._writer1, self._step5_model.get_model_data_arr())

        bktest_equity_curve_df = self.read_csv_data(self.get_bktest_equity_curve_filename(args))
        fwtest_equity_curve_df = self.read_csv_data(self.get_fwtest_equity_curve_filename(args))
        self._equity_curve_plotter.generate_combined_top_results_images_step5(top_rows_df, bktest_equity_curve_df, fwtest_equity_curve_df, args)

        self.cleanup()


def main():
    step = BacktestingStep5()
    step.run()


if __name__ == '__main__':
    main()