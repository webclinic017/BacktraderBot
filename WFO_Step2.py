'''
Step 3 of backtesting process
'''

import backtrader as bt
import backtrader.feeds as btfeeds

import argparse
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from extensions.sizers.cashsizer import FixedCashSizer
from datetime import datetime
from datetime import timedelta
from strategies.helper.utils import Utils
from config.strategy_enum import BTStrategyEnum
from common.stfetcher import StFetcher
from model.reports_common import ColumnName
from model.common import WFOTestingData, WFOCycleInfo, StrategyRunData, StrategyConfig
from model.backtestmodel import BacktestModel
from model.backtestmodelgenerator import BacktestModelGenerator
from model.common import WFOMode
from config.strategy_config import AppConfig
import os
import csv
import pandas as pd
import ast
import gc

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


class WFOStep2(object):

    _INDEX_ALL_KEYS_ARR = ["Strategy ID", "Exchange", "Currency Pair", "Timeframe", "Parameters"]
    _INDEX_STEP2_NUMBERS_ARR = [0, 1, 2, 3]

    def __init__(self):
        self._cerebro = None
        self._input_filename = None
        self.step1_df = None
        self._market_data_input_filename = None
        self._output_file1_full_name = None
        self._output_file2_full_name = None
        self._ofile1 = None
        self._ofile2 = None
        self._writer1 = None
        self._writer2 = None
        self._step2_model = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Walk Forward Optimization Step 2: Testing')

        parser.add_argument('-x', '--maxcpus',
                            type=int,
                            default=8,
                            choices=[1, 2, 3, 4, 5, 7, 8],
                            help='The max number of CPUs to use for processing')

        parser.add_argument('-l', '--lottype',
                            type=str,
                            default=AppConfig.get_global_lot_type(),
                            choices=["Percentage", "Fixed"],
                            help='Lot type')

        parser.add_argument('-z', '--lotsize',
                            type=int,
                            default=AppConfig.get_global_lot_size(),
                            help='Lot size: either percentage or number of units - depending on lottype parameter')

        parser.add_argument('--commtype',
                            default="Percentage",
                            type=str,
                            choices=["Percentage", "Fixed"],
                            help='The type of commission to apply to a trade')

        parser.add_argument('--commission',
                            default=0.002,
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('-r', '--runid',
                            type=str,
                            required=True,
                            help='Name of the output file(RunId****) from Step1')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def init_cerebro(self, runner, args, startcash):
        # Create an instance of cerebro
        self._cerebro = bt.Cerebro(optreturn=True, maxcpus=args.maxcpus, preload=True, cheat_on_open=True)

        self._cerebro.optcallback(runner.optimization_step)
        runner.cerebro = self._cerebro

        # Set our desired cash start
        self._cerebro.broker.setcash(startcash)

        # Add the analyzers we are interested in
        self._cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self._cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd", initial_cash=startcash)
        self._cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=startcash)

        # add the sizer
        if args.lottype != "" and args.lottype == "Percentage":
            self._cerebro.addsizer(VariablePercentSizer, percents=args.lotsize, debug=args.debug)
        else:
            self._cerebro.addsizer(FixedCashSizer, cashamount=args.lotsize, commission=args.commission)

        if args.commtype.lower() == 'percentage':
            self._cerebro.broker.setcommission(args.commission)

    def check_market_data_csv_has_data(self, filename, startdate, enddate):
        df = pd.read_csv(filename)
        for index, row in df.iterrows():
            timestamp_str = row['Timestamp']
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
            if startdate < timestamp and enddate < timestamp:
                print("!!! There is no market data for the start/end date range provided. Finishing execution.")
                quit()
            else:
                return True

    def get_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step1.csv'.format(dirname, args.runid, args.runid)

    def get_step1_equity_curve_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step1_EquityCurveData.csv'.format(dirname, args.runid, args.runid)

    def read_csv_data(self, filepath):
        df = pd.read_csv(filepath, index_col=self._INDEX_STEP2_NUMBERS_ARR)
        df = df.sort_index()
        return df

    def get_unique_index_values(self, df, name):
        return df.index.get_level_values(name).unique()

    def get_unique_index_value_lists(self, df):
        strat_list = self.get_unique_index_values(df, ColumnName.STRATEGY_ID)
        exc_list = self.get_unique_index_values(df, ColumnName.EXCHANGE)
        sym_list = self.get_unique_index_values(df, ColumnName.CURRENCY_PAIR)
        tf_list = self.get_unique_index_values(df, ColumnName.TIMEFRAME)
        return strat_list, exc_list, sym_list, tf_list

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename1(self, base_path, args):
        return '{}/{}_Step2.csv'.format(base_path, args.runid)

    def get_output_filename2(self, base_path, args):
        return '{}/{}_Step2_EquityCurveData.csv'.format(base_path, args.runid)

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

    def get_processing_daterange(self, data):
        result = {}

        range_splitted = data.split('-')
        start_date = range_splitted[0]
        end_date = range_splitted[1]
        s = datetime.strptime(start_date, '%Y%m%d')
        e = datetime.strptime(end_date, '%Y%m%d')

        result['fromyear'] = s.year
        result['frommonth'] = s.month
        result['fromday'] = s.day
        result['toyear'] = e.year
        result['tomonth'] = e.month
        result['today'] = e.day
        return result

    def get_fromdate(self, arr):
        fromyear = arr["fromyear"]
        frommonth = arr["frommonth"]
        fromday = arr["fromday"]
        return datetime(fromyear, frommonth, fromday)

    def get_todate(self, arr):
        toyear = arr["toyear"]
        tomonth = arr["tomonth"]
        today = arr["today"]
        return datetime(toyear, tomonth, today)

    def get_step1_key(self, strat, exch, sym, tf, params):
        return "{}-{}-{}-{}-{}".format(strat, exch, sym, tf, params)

    def get_marketdata_filename(self, exchange, symbol, timeframe):
        return './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(exchange, symbol, timeframe, exchange, symbol, timeframe)

    def add_datas(self, exchange, symbol, timeframe, fromdate, todate):
        data_tf = self.build_data(exchange, symbol, timeframe, fromdate, todate)

        # Add the data to Cerebro
        self._cerebro.adddata(data_tf, "data_{}".format(timeframe))

    def build_data(self, exchange, symbol, timeframe, fromdate, todate):
        fromdate_back_delta = timedelta(days=50)  # Adjust from date to add more candle data from the past to strategy to prevent any calculation problems with indicators
        granularity = Utils.get_granularity_by_tf_str(timeframe)
        timeframe_id = granularity[0][0]
        compression = granularity[0][1]
        fromdate_back = fromdate - fromdate_back_delta
        todate_delta = timedelta(days=2)  # Adjust to date to add more candle data
        todate_beyond = todate + todate_delta

        marketdata_filename = self.get_marketdata_filename(exchange, symbol, timeframe)
        return btfeeds.GenericCSVData(
            dataname=marketdata_filename,
            fromdate=fromdate_back,
            todate=todate_beyond,
            timeframe=timeframe_id,
            compression=compression,
            dtformat="%Y-%m-%dT%H:%M:%S",
            # nullvalue=0.0,
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            openinterest=-1
        )

    def get_parameters_map(self, parameters_json):
        return ast.literal_eval(parameters_json)

    def calc_startcash(self, model_row):
        if model_row and model_row.analyzer_data:
            return model_row.analyzer_data.startcash + model_row.analyzer_data.net_profit
        else:
            return AppConfig.get_global_default_cash_size()

    def enqueue_strategies(self, wfo_testing_model, wfo_cycle_id, wfo_testing_data, testing_startdate, testing_enddate, args):
        strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(wfo_testing_data.strategyid)
        for wfo_cycle_training_id, wfo_cycle_params_dict in wfo_testing_data.trained_params_dict.items():
            prev_cycle_run_model_row = wfo_testing_model.get_report_row_by_wfo_cycle(wfo_cycle_id - 1, wfo_cycle_training_id)
            startcash = self.calc_startcash(prev_cycle_run_model_row)
            testing_params = self.get_parameters_map(wfo_cycle_params_dict[wfo_cycle_id])
            testing_params.update({("debug",                 args.debug),
                                   ("wfo_cycle_id",          wfo_cycle_id),
                                   ("wfo_cycle_training_id", wfo_cycle_training_id),
                                   ("startcash", startcash),
                                   ("fromyear",  testing_startdate.year),
                                   ("frommonth", testing_startdate.month),
                                   ("fromday",   testing_startdate.day),
                                   ("toyear",    testing_enddate.year),
                                   ("tomonth",   testing_enddate.month),
                                   ("today",     testing_enddate.day)})
            strategy_class = strategy_enum.value.clazz
            StFetcher.register(strategy_class, **testing_params)

        print("Enqueued {} of strategies in Cerebro for WFO Testing Stage".format(len(StFetcher.COUNT())))
        self._cerebro.optstrategy(StFetcher, idx=StFetcher.COUNT())

    def cleanup_cerebro(self, runner):
        # Clean up and destroy cerebro
        runner.cerebro.runstop()
        runner.cerebro = None
        StFetcher.cleanall()
        gc.collect()

    def run_strategies(self, runner):
        # clock the start of the process
        tstart = datetime.now()
        tstart_str = tstart.strftime("%Y-%m-%d %H:%M:%S")

        print("!! Started current run at {}. Number of strategies={}".format(tstart_str, len(StFetcher.COUNT())))
        # Run over everything
        stratruns = runner.run_strategies()

        # clock the end of the process
        tend = datetime.now()
        tend_str = tend.strftime("%Y-%m-%d %H:%M:%S")

        print("Cerebro has processed {} strategies at {}".format(len(stratruns), tend_str))

        # Clean up and destroy cerebro
        runner.cerebro.runstop()
        runner.cerebro = None
        StFetcher.cleanall()
        gc.collect()

        return stratruns

    def parse_wfo_testing_data(self, df, strategy_list, exchange_list, symbol_list, timeframe_list):
        strategy = strategy_list[0]
        exchange = exchange_list[0]
        symbol = symbol_list[0]
        timeframe = timeframe_list[0]
        wfo_testing_data = WFOTestingData(strategy, exchange, symbol, timeframe)
        data_df = df.loc[[(strategy, exchange, symbol, timeframe)]]
        num_wfo_cycles = data_df[ColumnName.WFO_CYCLE_ID].max()
        num_trained_params = len(data_df.loc[data_df[ColumnName.WFO_CYCLE_ID] == 1])

        for wfo_cycle_id in range(1, num_wfo_cycles + 1):
            wfo_cycle_df = data_df.loc[data_df[ColumnName.WFO_CYCLE_ID] == wfo_cycle_id]
            cycle_first_row = wfo_cycle_df.iloc[0]
            wfo_training_period = cycle_first_row[ColumnName.WFO_TRAINING_PERIOD]
            wfo_testing_period = cycle_first_row[ColumnName.WFO_TESTING_PERIOD]
            training_daterange = self.get_processing_daterange(cycle_first_row[ColumnName.TRAINING_DATE_RANGE])
            testing_daterange = self.get_processing_daterange(cycle_first_row[ColumnName.TESTING_DATE_RANGE])
            wfo_cycle_info = WFOCycleInfo(wfo_cycle_id,
                                          wfo_training_period,
                                          wfo_testing_period,
                                          self.get_fromdate(training_daterange),
                                          self.get_todate(training_daterange),
                                          self.get_fromdate(testing_daterange),
                                          self.get_todate(testing_daterange))
            wfo_testing_data.set_wfo_cycle(wfo_cycle_info)
            for wfo_cycle_training_id in range(1, num_trained_params + 1):
                wfo_trained_data_df = wfo_cycle_df.iloc[wfo_cycle_training_id - 1]
                if wfo_cycle_training_id in wfo_testing_data.trained_params_dict:
                    wfo_cycle_params_dict = wfo_testing_data.trained_params_dict[wfo_cycle_training_id]
                else:
                    wfo_cycle_params_dict = dict()
                wfo_cycle_params_dict[wfo_cycle_id] = wfo_trained_data_df[ColumnName.PARAMETERS]
                wfo_testing_data.trained_params_dict[wfo_cycle_training_id] = wfo_cycle_params_dict

        return wfo_testing_data

    def run_wfo_testing(self, input_df, args):
        model_generator = BacktestModelGenerator(False)
        strat_list, exc_list, sym_list, tf_list = self.get_unique_index_value_lists(input_df)
        wfo_testing_data = self.parse_wfo_testing_data(input_df, strat_list, exc_list, sym_list, tf_list)
        wfo_cycles = list(wfo_testing_data.wfo_cycles_dict.values())
        wfo_testing_model = BacktestModel(WFOMode.WFO_MODE_TESTING, wfo_cycles)

        for strategy in strat_list:
            for exchange in exc_list:
                for symbol in sym_list:
                    for timeframe in tf_list:
                        num_wfo_cycles = wfo_testing_data.get_num_wfo_cycles()
                        strategy_run_data = StrategyRunData(strategy, exchange, symbol, timeframe)
                        for wfo_cycle_id in range(1, num_wfo_cycles + 1):
                            startcash = AppConfig.get_global_default_cash_size()
                            runner = CerebroRunner()
                            self.init_cerebro(runner, args, startcash)

                            wfo_cycle_info = wfo_testing_data.wfo_cycles_dict[wfo_cycle_id]
                            testing_startdate = wfo_cycle_info.testing_start_date
                            testing_enddate = wfo_cycle_info.testing_end_date
                            self._market_data_input_filename = self.get_marketdata_filename(exchange, symbol, timeframe)
                            self.check_market_data_csv_has_data(self._market_data_input_filename, testing_startdate, testing_enddate)
                            self.add_datas(exchange, symbol, timeframe, testing_startdate, testing_enddate)
                            self.enqueue_strategies(wfo_testing_model, wfo_cycle_id, wfo_testing_data, testing_startdate, testing_enddate, args)

                            print("\n******** Running WFO Testing: {} iterations over {} WFO cycles for {}/{}/{}/{} ********".format(wfo_testing_data.get_num_trained_params(),
                                                                                                                                     wfo_testing_data.get_num_wfo_cycles(),
                                                                                                                                     strategy, exchange, symbol, timeframe))
                            run_results = self.run_strategies(runner)

                            curr_wfo_cycle_info = wfo_testing_data.wfo_cycles_dict[wfo_cycle_id]
                            strategy_config = StrategyConfig()
                            strategy_config.lotsize = args.lotsize
                            strategy_config.lottype = args.lottype
                            wfo_testing_model = model_generator.populate_model_data(wfo_testing_model, strategy_run_data, strategy_config, curr_wfo_cycle_info, run_results)

        wfo_testing_model.sort_wfo_testing_results()
        return wfo_testing_model

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

        self.step1_df = self.read_csv_data(self._input_filename)

        self.init_output_files(args)

        print("Writing WFO Step 2 results to: {}".format(self._output_file1_full_name))

        self._step2_model = self.run_wfo_testing(self.step1_df, args)

        self.printfinalresultsheader(self._writer1, self._step2_model)

        print("Writing WFO Step 2 equity curve data to: {}".format(self._output_file2_full_name))

        self.printequitycurvedataheader(self._writer2, self._step2_model)

        self.printfinalresults(self._writer1, self._step2_model)

        self.printequitycurvedataresults(self._writer2, self._step2_model)

        self.cleanup()

def main():
    step = WFOStep2()
    step.run()

if __name__ == '__main__':
    main()