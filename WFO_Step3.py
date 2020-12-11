'''
Step 3 of WFO process
'''

import argparse
from datetime import datetime
from model.reports_common import ColumnName
from model.common import WFOTestingData, WFOCycleInfo, StrategyRunData
from model.step3model import Step3Model
from model.step3avgmodel import Step3AvgModel
from model.step3modelgenerator import Step3ModelGenerator
from plotting.equity_curve import EquityCurvePlotter
from wfo.wfo_helper import WFOHelper
import os
import csv
import pandas as pd

string_types = str


class CerebroRunner(object):
    cerebro = None

    _DEBUG_MEMORY_STATS = False

    _batch_number = 0

    def optimization_step(self, strat):
        self._batch_number += 1
        st = strat[0]
        st.strat_id = self._batch_number
        print('!! Finished Batch Run={}'.format(self._batch_number))

    def run_strategies(self):
        # Run over everything
        return self.cerebro.run()


class WFOStep3(object):

    _INDEX_ALL_KEYS_ARR = ["Strategy ID", "Exchange", "Currency Pair", "Timeframe", "Parameters"]
    _INDEX_STEP2_NUMBERS_ARR = [0, 1, 2, 3]

    def __init__(self):
        self._cerebro = None
        self._input_filename = None
        self._equity_curve_input_filename = None
        self._step2_df = None
        self._equity_curve_df = None
        self._market_data_input_filename = None
        self._output_file1_full_name = None
        self._output_file2_full_name = None
        self._output_file3_full_name = None
        self._ofile1 = None
        self._ofile2 = None
        self._ofile3 = None
        self._writer1 = None
        self._writer2 = None
        self._writer3 = None
        self._step3_model = None
        self._step3_avg_model = None

        self._equity_curve_plotter = EquityCurvePlotter("Step3")

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Walk Forward Optimization Step 3')

        parser.add_argument('-x', '--maxcpus',
                            type=int,
                            default=8,
                            choices=[1, 2, 3, 4, 5, 7, 8],
                            help='The max number of CPUs to use for processing')

        parser.add_argument('-r', '--runid',
                            type=str,
                            required=True,
                            help='Name of the output file(RunId****) from Step2')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def get_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step2.csv'.format(dirname, args.runid, args.runid)

    def get_step2_equity_curve_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step2_EquityCurveData.csv'.format(dirname, args.runid, args.runid)

    def read_csv_data(self, filepath):
        df = pd.read_csv(filepath, index_col=self._INDEX_STEP2_NUMBERS_ARR)
        df = df.sort_index()
        return df

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename1(self, base_path, args):
        return '{}/{}_Step3.csv'.format(base_path, args.runid)

    def get_output_filename2(self, base_path, args):
        return '{}/{}_Step3_EquityCurveData.csv'.format(base_path, args.runid)

    def get_output_filename3(self, base_path, args):
        return '{}/{}_Step3_AvgData.csv'.format(base_path, args.runid)

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def init_output_files(self, args):
        base_dir = self.whereAmI()
        output_path = self.get_output_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)

        self._output_file1_full_name = self.get_output_filename1(output_path, args)
        self._ofile1 = open(self._output_file1_full_name, "w")
        self._writer1 = csv.writer(self._ofile1, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        self._output_file2_full_name = self.get_output_filename2(output_path, args)
        self._ofile2 = open(self._output_file2_full_name, "w")
        self._writer2 = csv.writer(self._ofile2, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        self._output_file3_full_name = self.get_output_filename3(output_path, args)
        self._ofile3 = open(self._output_file3_full_name, "w")
        self._writer3 = csv.writer(self._ofile3, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    def combine_wfo_testing_data(self, wfo_testing_data, input_df, equity_curve_df):
        model_generator = Step3ModelGenerator()
        strat_list, exc_list, sym_list, tf_list = WFOHelper.get_unique_index_value_lists(input_df)
        step3_model = Step3Model()

        for strategy in strat_list:
            for exchange in exc_list:
                for symbol in sym_list:
                    for timeframe in tf_list:
                        num_training_ids = wfo_testing_data.get_num_training_ids()
                        strategy_run_data = StrategyRunData(strategy, exchange, symbol, timeframe)
                        for training_id in range(1, num_training_ids + 1):
                            key_df = input_df.loc[(strategy, exchange, symbol, timeframe)]
                            rows_df = key_df.loc[key_df[ColumnName.WFO_CYCLE_TRAINING_ID] == training_id]
                            key_equity_curve_df = equity_curve_df.loc[(strategy, exchange, symbol, timeframe)]
                            equity_curve_rows_df = key_equity_curve_df.loc[key_equity_curve_df[ColumnName.WFO_CYCLE_TRAINING_ID] == training_id]
                            step3_model = model_generator.populate_model_data(step3_model, wfo_testing_data, strategy_run_data, training_id, rows_df, equity_curve_rows_df)
        return step3_model

    def calculate_avg_data(self, step3_model):
        model_generator = Step3ModelGenerator()
        step3_df = step3_model.get_model_df()
        step3_equity_curve_df = step3_model.get_equity_curve_model_df()
        step3_avg_model = Step3AvgModel()
        strat_list, exc_list, sym_list, tf_list = WFOHelper.get_unique_index_value_lists(step3_df)

        for strategy in strat_list:
            for exchange in exc_list:
                for symbol in sym_list:
                    for timeframe in tf_list:
                        strategy_run_data = StrategyRunData(strategy, exchange, symbol, timeframe)
                        rows_df = step3_df.loc[(strategy, exchange, symbol, timeframe)]
                        equity_curve_rows_df = step3_equity_curve_df.loc[(strategy, exchange, symbol, timeframe)]
                        step3_avg_model = model_generator.populate_avg_model_data(step3_avg_model, strategy_run_data, rows_df, equity_curve_rows_df)
        return step3_avg_model

    def printfinalresultsheader(self, writer, model):
        # Designate the rows
        h1 = model.get_header_names()

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def printequitycurvedataheader(self, writer, model):
        # Designate the rows
        h1 = model.get_equity_curve_header_names()

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def printfinalresults(self, writer, model):
        print_list = model.get_model_data_arr()
        print("Writing {} rows...".format(len(print_list)))
        for item in print_list:
            writer.writerow(item)

    def printequitycurvedataresults(self, writer, model):
        print_list = model.get_equity_curve_report_data_arr()
        for item in print_list:
            writer.writerow(item)

    def cleanup(self):
        self._ofile1.close()
        self._ofile2.close()

    def run(self):
        args = self.parse_args()

        self._input_filename = self.get_input_filename(args)
        self._equity_curve_input_filename = self.get_step2_equity_curve_filename(args)

        self._step2_df = self.read_csv_data(self._input_filename)
        self._equity_curve_df = self.read_csv_data(self._equity_curve_input_filename)

        self.init_output_files(args)

        print("Writing WFO Step 3 results into: {}".format(self._output_file1_full_name))

        wfo_testing_data = WFOHelper.parse_wfo_testing_data(self._step2_df)
        self._step3_model = self.combine_wfo_testing_data(wfo_testing_data, self._step2_df, self._equity_curve_df)
        self._step3_avg_model = self.calculate_avg_data(self._step3_model)

        print("Writing WFO Step 3 equity curve data to: {}".format(self._output_file2_full_name))

        self.printfinalresultsheader(self._writer1, self._step3_model)
        self.printequitycurvedataheader(self._writer2, self._step3_model)
        self.printfinalresultsheader(self._writer3, self._step3_avg_model)

        self.printfinalresults(self._writer1, self._step3_model)
        self.printequitycurvedataresults(self._writer2, self._step3_model)
        self.printfinalresults(self._writer3, self._step3_avg_model)

        self._equity_curve_plotter.generate_images_step3(wfo_testing_data, self._step3_model.get_model_df(), self._step3_model.get_equity_curve_model_df(), self._step3_avg_model.get_equity_curve_model_df(), args)

        self.cleanup()


def main():
    step = WFOStep3()
    step.run()


if __name__ == '__main__':
    main()
