'''
Step 2 of backtesting process
'''
 
import argparse
from model.backtestingstep1 import BacktestingStep1Model
import os
import csv
import pandas as pd

class BacktestingStep2(object):

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

    def printfinalresultsheader(self, writer, model):

        # Designate the rows
        h1 = model.get_header_names()

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def generate_results_list(self, args):
        # Generate results list
        model = BacktestingStep1Model(args.fromyear, args.frommonth, args.toyear, args.tomonth)
        for run in stratruns:
            for strategy in run:
                # print the analyzers
                ta_analysis = strategy.analyzers.ta.get_analysis()
                sqn_analysis = strategy.analyzers.sqn.get_analysis()
                dd_analysis = strategy.analyzers.dd.get_analysis()

                strat_key = strategy.strat_id
                parameters = self.getparametersstr(strategy.params)
                monthly_stats = ta_analysis.monthly_stats if self.exists(ta_analysis, ['monthly_stats']) else {}
                num_months = model.get_num_months()
                total_closed = ta_analysis.total.closed if self.exists(ta_analysis, ['total', 'closed']) else 0
                net_profit = round(ta_analysis.pnl.netprofit.total, 8) if self.exists(ta_analysis, ['pnl', 'netprofit',
                                                                                                    'total']) else 0
                net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total / startcash, 2) if self.exists(ta_analysis,
                                                                                                            ['pnl',
                                                                                                             'netprofit',
                                                                                                             'total']) else 0
                avg_monthly_net_profit_pct = '{}%'.format(
                    self.get_avg_monthly_net_profit_pct(monthly_stats, num_months))
                total_won = ta_analysis.won.total if self.exists(ta_analysis, ['won', 'total']) else 0
                strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
                max_drawdown_pct = round(dd_analysis.max.drawdown, 2)
                max_drawdown_length = round(dd_analysis.max.len, 2)
                num_winning_months = '{}%'.format(self.get_num_winning_months(monthly_stats, num_months))
                profitfactor = round(ta_analysis.total.profitfactor, 3) if self.exists(ta_analysis,
                                                                                       ['total', 'profitfactor']) else 0
                buyandhold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if self.exists(ta_analysis,
                                                                                                       ['total',
                                                                                                        'buyandholdreturnpct']) else 0
                sqn_number = round(sqn_analysis.sqn, 2)
                monthlystatsprefix = args.monthlystatsprefix
                netprofitsdata = ta_analysis.total.netprofitsdata

                if net_profit > 0 and total_closed > 0:
                    model.add_result_row(args.strategy, args.exchange, args.symbol, args.timeframe, parameters,
                                         self.getdaterange(args), self.getlotsize(args), total_closed, net_profit,
                                         net_profit_pct, avg_monthly_net_profit_pct, max_drawdown_pct,
                                         max_drawdown_length, strike_rate, num_winning_months, profitfactor,
                                         buyandhold_return_pct, sqn_number, monthlystatsprefix, monthly_stats,
                                         netprofitsdata)

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

        step1_df = pd.read_csv(self._input_filename, index_col=[0, 1, 2])
        step1_df = step1_df.sort_index()
        exc_list = step1_df.index.get_level_values('Exchange').unique()
        sym_list = step1_df.index.get_level_values('Currency Pair').unique()
        tf_list = step1_df.index.get_level_values('Timeframe').unique()

        self.init_output_files(args)

        print("Writing Step2 backtesting run results to: {}".format(self._output_file1_full_name))

        self._step2_model = self.generate_results_list(args)

        self.printfinalresultsheader(self._writer1, self._step2_model)

        self._step2_model.sort_results()

        self.printfinalresults(self._writer1, self._step2_model.get_model_data_arr())

        self.cleanup()


def main():
    step = BacktestingStep2()
    step.run()


if __name__ == '__main__':
    main()