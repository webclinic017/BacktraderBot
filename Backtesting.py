'''
Backtesting process
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
from config.strategy_config import AppConfig
from config.strategy_enum import BTStrategyEnum
from model.backtestmodel import BacktestModel
from model.backtestmodelgenerator import BacktestModelGenerator
from common.stfetcher import StFetcher
from strategies.helper.validation import ParametersValidator
from strategies.helper.utils import Utils
from wfo.wfo_helper import WFOHelper
from model.common import WFOMode, StrategyRunData, StrategyConfig
from model.reports_common import ColumnName
import itertools
import collections
import os
import csv
import pandas as pd
import objgraph
import sys
from numbers import Number
from collections.abc import Set, Mapping
from collections import deque
from plotting.equity_curve import EquityCurvePlotter
import gc

NUMBER_TOP_ROWS = None  # 100
TOP_ROWS_IN_CYCLE_TO_RENDER = None  # 20

zero_depth_bases = (str, bytes, Number, range, bytearray)
iteritems = 'items'
string_types = str


class CerebroRunner(object):

    cerebro = None

    _DEBUG_MEMORY_STATS = False

    _batch_number = 0

    def getsize(self, obj_0):
        """Recursively iterate to sum size of object & members."""
        _seen_ids = set()

        def inner(obj):
            obj_id = id(obj)
            if obj_id in _seen_ids:
                return 0
            _seen_ids.add(obj_id)
            size = sys.getsizeof(obj)
            if isinstance(obj, zero_depth_bases):
                pass  # bypass remaining control flow and return
            elif isinstance(obj, (tuple, list, Set, deque)):
                size += sum(inner(i) for i in obj)
            elif isinstance(obj, Mapping) or hasattr(obj, iteritems):
                size += sum(inner(k) + inner(v) for k, v in getattr(obj, iteritems)())
            # Check for custom object instances - may subclass above too
            if hasattr(obj, '__dict__'):
                size += inner(vars(obj))
            if hasattr(obj, '__slots__'):  # can have __slots__ with __dict__
                size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
            return size

        return inner(obj_0)

    def print_debug_memory_stats(self):
        if self._DEBUG_MEMORY_STATS is True:
            obj = objgraph.by_type('Cerebro')
            print ("Current cerebro={}, size={}, len(cerebro.runstrats)={}, self.getsize(self.cerebro.runstrats[-1])={}".format(hex(id(self.cerebro)), self.getsize(self.cerebro), len(self.cerebro.runstrats), self.getsize(self.cerebro.runstrats[-1])))
            print("!!! len(obj)={}".format(len(obj)))
            print("!!! obj={}".format(obj))
            print("!!! getsize(obj)={}".format(self.getsize(obj)))
            for ob in obj:
                print("ob={}, self.getsize(ob)={}".format(hex(id(ob)), self.getsize(ob)))
            #objgraph.show_backrefs(obj, max_depth=8, filename='backref-graph.png', filter=lambda x: not inspect.isclass(x), refcounts=True)
            #gc.collect()
            #objgraph.show_refs(self.cerebro.runstrats[-1], max_depth=8, filename='memory_chain{:03d}.png'.format(self._batch_number), filter=lambda x: not inspect.isclass(x), refcounts=True)

    def optimization_step(self, strat):
        self._batch_number += 1
        st = strat[0]
        st.strat_id = self._batch_number
        print('!! Finished Batch Run={}'.format(self._batch_number))
        self.print_debug_memory_stats()

    def run_strategies(self):
        # Run over everything
        return self.cerebro.run()


class Backtesting(object):

    _INDEX_NUMBERS_ARR = [0, 1, 2, 3, 4]

    _ENABLE_FILTERING = AppConfig.is_global_step1_enable_filtering()

    def __init__(self):
        self._cerebro = None
        self._params = None
        self. _is_output_file1_exists = None
        self._is_output_file2_exists = None
        self._market_data_input_filename = None
        self._output_file1_full_name = None
        self._output_file2_full_name = None
        self._ofile1 = None
        self._ofile2 = None
        self._writer1 = None
        self._writer2 = None
        self._step1_model = None

        self._equity_curve_plotter = EquityCurvePlotter("Backtesting")

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtesting process')

        parser.add_argument('-r', '--runid',
                            type=str,
                            default="",
                            required=True,
                            help='Run ID')

        parser.add_argument('--startyear',
                            type=int,
                            required=True,
                            help='Date Range: Start Year')

        parser.add_argument('--startmonth',
                            type=int,
                            required=True,
                            help='Date Range: Start Month')

        parser.add_argument('--startday',
                            type=int,
                            required=True,
                            help='Date Range: Start Day')

        parser.add_argument('--wfo_training_period',
                            type=int,
                            required=False,
                            default=85,
                            help='WFO training (in-sample) period length in days')

        parser.add_argument('-y', '--strategy',
                            type=str,
                            required=True,
                            help='The strategy ID')

        parser.add_argument('-e', '--exchange',
                            type=str,
                            required=True,
                            help='The exchange name')

        parser.add_argument('-s', '--symbol',
                            type=str,
                            required=True,
                            help='The Symbol/Currency Pair To Process')

        parser.add_argument('-t', '--timeframe',
                            type=str,
                            required=True,
                            help='The timeframe')

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

        parser.add_argument('--commsizer',
                            action='store_true', help=('Use the Sizer '
                                                       'that takes commissions into account'))

        parser.add_argument('--commtype',
                            default="Percentage",
                            type=str,
                            choices=["Percentage", "Fixed"],
                            help='The type of commission to apply to a trade')

        parser.add_argument('--commission',
                            default=AppConfig.get_global_default_commission(),
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('--risk',
                            default=AppConfig.get_global_default_risk(),
                            type=float,
                            help='The percentage of capital to risk on a trade')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def cleanup_cerebro(self, runner):
        # Clean up cerebro
        runner.cerebro = None
        StFetcher.cleanall()
        gc.collect()

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
            self._cerebro.addsizer(FixedCashSizer, lotsize=args.lotsize, commission=args.commission, risk=args.risk)

        if args.commtype.lower() == 'percentage':
            self._cerebro.broker.setcommission(args.commission)

    def get_strategy_enum(self, args):
        return BTStrategyEnum.get_strategy_enum_by_str(args.strategy)

    def init_params(self, strat_enum, args, startcash, wfo_cycle_info):
        training_start_date = wfo_cycle_info.training_start_date.date()
        training_end_date = wfo_cycle_info.training_end_date.date()
        self._params = AppConfig.get_step1_strategy_params(strat_enum).copy()
        self._params.update({("debug", args.debug),
                             ("startcash", startcash),
                             ("fromyear", training_start_date.year),
                             ("toyear", training_end_date.year),
                             ("frommonth", training_start_date.month),
                             ("tomonth", training_end_date.month),
                             ("fromday", training_start_date.day),
                             ("today", training_end_date.day)})

    def get_marketdata_filename(self, exchange, symbol, timeframe):
        return './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(exchange, symbol, timeframe, exchange, symbol, timeframe)

    @staticmethod
    def iterize(iterable):
        niterable = list()
        for elem in iterable:
            if isinstance(elem, string_types):
                elem = (elem,)
            elif not isinstance(elem, collections.abc.Iterable):
                elem = (elem,)

            niterable.append(elem)

        return niterable

    def get_wfo_cycles(self, args):
        start_date = self.get_wfo_startdate(args)
        return WFOHelper.get_wfo_cycles(start_date, 1, args.wfo_training_period, 15)

    def validate_strategy_params(self, params_dict):
        try:
            return ParametersValidator.validate_params(params_dict)
        except ValueError as ve:
            return False

    def update_params(self, curr_wfo_cycle_info):
        self._params.update({("wfo_cycle_id", curr_wfo_cycle_info.wfo_cycle_id)})

    def enqueue_strategies(self, strategy_enum):
        strategy_class = strategy_enum.value.clazz

        kwargz = self._params
        optkeys = list(self._params)
        vals = self.iterize(kwargz.values())
        optvals = itertools.product(*vals)
        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)
        optkwargs = map(dict, okwargs1)
        list_strat_params = list(optkwargs)

        for params in list_strat_params:
            if self.validate_strategy_params(params):
                StFetcher.register(strategy_class, **params)

        print("Number of strategies: {}".format(len(StFetcher.COUNT())))
        self._cerebro.optstrategy(StFetcher, idx=StFetcher.COUNT())


    def check_market_data_csv_has_data(self, filename, wfo_cycle_info):
        df = pd.read_csv(filename)
        fromdate = wfo_cycle_info.training_start_date
        todate = wfo_cycle_info.training_end_date
        for index, row in df.iterrows():
            timestamp_str = row['Timestamp']
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
            if fromdate < timestamp and todate < timestamp:
                print("!!! There is no market data for the start/end date range provided. Finishing execution.")
                quit()
            else:
                return True

    def get_input_filename(self, args):
        return './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(args.exchange, args.symbol, args.timeframe, args.exchange, args.symbol, args.timeframe)

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename1(self, base_path, args):
        return '{}/{}_Backtesting.csv'.format(base_path, args.runid)

    def get_output_filename2(self, base_path, args):
        return '{}/{}_Backtesting_EquityCurveData.csv'.format(base_path, args.runid)

    def get_wfo_startdate(self, args):
        return datetime(args.startyear, args.startmonth, args.startday)

    def add_datas(self, args, wfo_cycle_info):
        fromdate = wfo_cycle_info.training_start_date.date()
        todate = wfo_cycle_info.training_end_date.date()

        data_tf = self.build_data(fromdate, todate, args.exchange, args.symbol, args.timeframe)

        # Add the data to Cerebro
        self._cerebro.adddata(data_tf, "data_{}".format(args.timeframe))

    def build_data(self, fromdate, todate, exchange, symbol, timeframe):
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

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def check_outputfile_exists(self):
        return os.path.exists(self._output_file1_full_name)

    def read_csv_data(self, filename):
        return pd.read_csv(filename, index_col=self._INDEX_NUMBERS_ARR)

    def init_output_files(self, args):
        base_dir = self.whereAmI()
        output_path = self.get_output_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)

        self._output_file1_full_name = self.get_output_filename1(output_path, args)
        if os.path.exists(self._output_file1_full_name):
            self._is_output_file1_exists = True
        else:
            self._is_output_file1_exists = False

        self._ofile1 = open(self._output_file1_full_name, "a")
        self._writer1 = csv.writer(self._ofile1, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        self._output_file2_full_name = self.get_output_filename2(output_path, args)
        if os.path.exists(self._output_file2_full_name):
            self._is_output_file2_exists = True
        else:
            self._is_output_file2_exists = False

        self._ofile2 = open(self._output_file2_full_name, "a")
        self._writer2 = csv.writer(self._ofile2, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    def run_strategies(self, runner):
        # Run over everything
        return runner.run_strategies()

    def create_model(self, wfo_cycles, curr_wfo_cycle_info, run_results, args):
        model = BacktestModel(WFOMode.WFO_MODE_TRAINING, wfo_cycles)
        generator = BacktestModelGenerator(self._ENABLE_FILTERING)
        strategy_run_data = StrategyRunData(args.strategy, args.exchange, args.symbol, args.timeframe)
        strategy_config = StrategyConfig()
        strategy_config.lotsize = args.lotsize
        strategy_config.lottype = args.lottype
        model = generator.populate_model_data(model, strategy_run_data, strategy_config, curr_wfo_cycle_info, run_results)
        model.filter_wfo_training_top_results(NUMBER_TOP_ROWS)
        return model

    def printfinalresultsheader(self, writer, model):
        if self._is_output_file1_exists is True:
            return

        # Designate the rows
        h1 = model.get_header_names()

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def printequitycurvedataheader(self, writer, model):
        if self._is_output_file2_exists is True:
            return

        # Designate the rows
        h1 = model.get_equity_curve_header_names()

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def printfinalresults(self, writer, arr):
        print_list = []
        print_list.extend(arr)
        print("Writing {} rows...".format(len(print_list)))
        for item in print_list:
            writer.writerow(item)
        self._ofile1.flush()

    def printequitycurvedataresults(self, writer, arr):
        print_list = []
        print_list.extend(arr)
        for item in print_list:
            writer.writerow(item)

    def generate_equitycurve_images(self, model, args):
        results_df = model.get_model_df().reset_index(drop=False)
        equity_curve_df = model.get_equity_curve_model_df()
        if TOP_ROWS_IN_CYCLE_TO_RENDER:
            results_df = results_df[results_df[ColumnName.WFO_CYCLE_TRAINING_ID] <= TOP_ROWS_IN_CYCLE_TO_RENDER]
            equity_curve_df = equity_curve_df[equity_curve_df[ColumnName.WFO_CYCLE_TRAINING_ID] <= TOP_ROWS_IN_CYCLE_TO_RENDER]
        if AppConfig.is_global_step1_enable_equitycurve_img_generation():
            self._equity_curve_plotter.generate_images_step1(results_df, equity_curve_df, args)

    def cleanup(self):
        self._ofile1.close()
        self._ofile2.close()

    def run(self):
        args = self.parse_args()

        strategy_enum = self.get_strategy_enum(args)

        startcash = AppConfig.get_global_default_cash_size()

        wfo_cycles = self.get_wfo_cycles(args)
        curr_wfo_cycle_info = wfo_cycles[0]
        training_start_date = curr_wfo_cycle_info.training_start_date.date()
        training_end_date = curr_wfo_cycle_info.training_end_date.date()
        print("\nRunning Backtesting - Training period {}".format(WFOHelper.getdaterange(training_start_date, training_end_date)))

        self.init_params(strategy_enum, args, startcash, curr_wfo_cycle_info)

        self.init_output_files(args)

        print("Writing Backtesting results into: {}".format(self._output_file1_full_name))

        runner = CerebroRunner()
        self.cleanup_cerebro(runner)
        self.init_cerebro(runner, args, startcash)

        self._market_data_input_filename = self.get_input_filename(args)

        self.check_market_data_csv_has_data(self._market_data_input_filename, curr_wfo_cycle_info)

        self.add_datas(args, curr_wfo_cycle_info)

        self.update_params(curr_wfo_cycle_info)

        self.enqueue_strategies(strategy_enum)

        run_results = self.run_strategies(runner)

        self._step1_model = self.create_model(wfo_cycles, curr_wfo_cycle_info, run_results, args)

        self.printfinalresultsheader(self._writer1, self._step1_model)

        self.printequitycurvedataheader(self._writer2, self._step1_model)

        self.printfinalresults(self._writer1, self._step1_model.get_model_data_arr())

        self.printequitycurvedataresults(self._writer2, self._step1_model.get_equity_curve_report_data_arr())

        self.generate_equitycurve_images(self._step1_model, args)

        self.cleanup()


def main():
    step = Backtesting()
    step.run()


if __name__ == '__main__':
    main()
