'''
Step 3 of backtesting process
'''

import backtrader as bt
import backtrader.feeds as btfeeds

import argparse
from backtrader import TimeFrame
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from extensions.sizers.cashsizer import FixedCashSizer
from datetime import datetime
from datetime import timedelta
from config.strategy_enum import BTStrategyEnum
from model.backtestmodel import BacktestModel
from model.step3model import Step3Model
from common.stfetcher import StFetcher
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


class BacktestingStep3(object):

    _INDEX_STEP2_NUMBERS_ARR = [0, 1, 2, 3]

    DEFAULT_STARTCASH_VALUE = 100000
    DEFAULT_LOT_SIZE = 98000

    _cerebro = None
    _input_filename = None
    _step2_df = None
    _market_data_input_filename = None
    _output_file1_full_name = None
    _output_file2_full_name = None
    _ofile1 = None
    _ofile2 = None
    _writer1 = None
    _writer2 = None
    _step3_model = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtesting Step 3')

        parser.add_argument('-d', '--testdaterange',
                            type=str,
                            required=True,
                            help='Step3 testing date range in the following format (startdate-enddate): \"YYYYMMDD-YYYYMMDD\"')

        parser.add_argument('-x', '--maxcpus',
                            type=int,
                            default=8,
                            choices=[1, 2, 3, 4, 5, 7, 8],
                            help='The max number of CPUs to use for processing')

        parser.add_argument('-l', '--lottype',
                            type=str,
                            default="Fixed",
                            required=True,
                            choices=["Percentage", "Fixed"],
                            help='Lot type')

        parser.add_argument('-z', '--lotsize',
                            type=int,
                            default=self.DEFAULT_LOT_SIZE,
                            help='Lot size: either percentage or number of units - depending on lottype parameter')

        parser.add_argument('--commtype',
                            default="Percentage",
                            type=str,
                            choices=["Percentage", "Fixed"],
                            help='The type of commission to apply to a trade')

        parser.add_argument('--commission',
                            default=0.0015,
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('-r', '--runid',
                            type=str,
                            required=True,
                            help='Name of the output file(RunId****) from Step1')

        parser.add_argument('-p', '--columnnameprefix',
                            type=str,
                            required=True,
                            help='The string to append to all columns in report')

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
            self._cerebro.addsizer(VariablePercentSizer, percents=98, debug=args.debug)
        else:
            self._cerebro.addsizer(FixedCashSizer, cashamount=args.lotsize)

        if args.commtype.lower() == 'percentage':
            self._cerebro.broker.setcommission(args.commission)

    def check_market_data_csv_has_data(self, filename, daterange):
        df = pd.read_csv(filename)
        startdate = self.get_fromdate(daterange)
        enddate = self.get_todate(daterange)
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
        return '{}/strategyrun_results/{}/{}_Step2.csv'.format(dirname, args.runid, args.runid)

    def read_csv_data(self, filepath):
        df = pd.read_csv(filepath, index_col=self._INDEX_STEP2_NUMBERS_ARR)
        df = df.sort_index()
        return df

    def get_unique_index_values(self, df, name):
        return df.index.get_level_values(name).unique()

    def get_unique_index_value_lists(self, df):
        strat_list = self.get_unique_index_values(df, 'Strategy ID')
        exc_list = self.get_unique_index_values(df, 'Exchange')
        sym_list = self.get_unique_index_values(df, 'Currency Pair')
        tf_list = self.get_unique_index_values(df, 'Timeframe')
        return strat_list, exc_list, sym_list, tf_list

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename1(self, base_path, args):
        return '{}/{}_Step3.csv'.format(base_path, args.runid)

    def get_output_filename2(self, base_path, args):
        return '{}/{}_Step3_EquityCurveData.csv'.format(base_path, args.runid)

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

    def add_data_to_cerebro(self, filename, daterange):
        fromdate = self.get_fromdate(daterange)
        todate = self.get_todate(daterange)

        fromdate_back_delta = timedelta(days=50)  # Adjust from date to add more candle data from the past to strategy to prevent any calculation problems with indicators
        fromdate_back = fromdate - fromdate_back_delta
        todate_delta = timedelta(days=2)  # Adjust to date to add more candle data
        todate_beyond = todate + todate_delta

        data = btfeeds.GenericCSVData(
            dataname=filename,
            fromdate=fromdate_back,
            todate=todate_beyond,
            timeframe=TimeFrame.Ticks,
            # compression=15,
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

        # Add the data to Cerebro
        self._cerebro.adddata(data)

    def get_parameters_map(self, parameters_json):
        return ast.literal_eval(parameters_json)

    def calc_startcash(self, netprofit):
        return self.DEFAULT_STARTCASH_VALUE + netprofit

    def enqueue_strategies(self, df, strategy_enum, proc_daterange, args):
        for index, data_row in df.iterrows():
            step3_params = self.get_parameters_map(data_row['Parameters'])
            step2_netprofit = data_row['Net Profit']
            startcash = self.calc_startcash(step2_netprofit)
            step3_params.update({("debug", args.debug),
                                 ("startcash", startcash),
                                 ("fromyear", proc_daterange["fromyear"]),
                                 ("frommonth", proc_daterange["frommonth"]),
                                 ("fromday", proc_daterange["fromday"]),
                                 ("toyear", proc_daterange["toyear"]),
                                 ("tomonth", proc_daterange["tomonth"]),
                                 ("today", proc_daterange["today"])})
            strategy_class = strategy_enum.value.clazz
            StFetcher.register(strategy_class, **step3_params)

        print("Enqueued {} of strategies in Cerebro".format(len(StFetcher.COUNT())))
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

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def getdaterange(self, daterange_arr):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(daterange_arr["fromyear"], daterange_arr["frommonth"], daterange_arr["fromday"],
                                                      daterange_arr["toyear"], daterange_arr["tomonth"], daterange_arr["today"])

    def getlotsize(self, args):
        return "Lot{}{}".format(args.lotsize, "Pct" if args.lottype == "Percentage" else "")

    def getparametersstr(self, params):
        coll = vars(params).copy()
        del coll["debug"]
        del coll["startcash"]
        del coll["fromyear"]
        del coll["frommonth"]
        del coll["fromday"]
        del coll["toyear"]
        del coll["tomonth"]
        del coll["today"]
        return "{}".format(coll)

    def get_avg_monthly_net_profit_pct(self, monthly_stats, num_months):
        sum_netprofits = 0
        for key, val in monthly_stats.items():
            curr_netprofit = val.pnl.netprofit.total
            sum_netprofits += curr_netprofit
        return round(sum_netprofits / float(num_months) if num_months > 0 else 0, 2)

    def get_num_winning_months(self, monthly_stats, num_months):
        num_positive_netprofit_months = 0
        for key, val in monthly_stats.items():
            curr_netprofit = val.pnl.netprofit.total
            if curr_netprofit > 0:
                num_positive_netprofit_months += 1
        return round(num_positive_netprofit_months * 100 / float(num_months) if num_months > 0 else 0, 2)

    def update_monthly_stats(self, stats, num_months):
        if len(stats) > 0:
            # Workaround: delete the last element of stats array - do not need to see last month of the whole calculation
            if len(stats) == num_months + 1:
                stats.popitem()

        return stats

    def append_model(self, model, strategy_id, exchange, symbol, timeframe, run_results, args, proc_daterange):
        # Generate results list
        for run in run_results:
            for strat in run:
                startcash = strat.params.startcash
                # print the analyzers
                ta_analysis = strat.analyzers.ta.get_analysis()
                sqn_analysis = strat.analyzers.sqn.get_analysis()
                dd_analysis = strat.analyzers.dd.get_analysis()

                parameters = self.getparametersstr(strat.params)
                monthly_stats = ta_analysis.monthly_stats if self.exists(ta_analysis, ['monthly_stats']) else {}
                num_months = model.get_num_months()
                monthly_stats = self.update_monthly_stats(monthly_stats, num_months)
                total_closed = ta_analysis.total.closed if self.exists(ta_analysis, ['total', 'closed']) else 0
                net_profit = round(ta_analysis.pnl.netprofit.total, 8) if self.exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total / startcash, 2) if self.exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                avg_monthly_net_profit_pct = '{}%'.format(self.get_avg_monthly_net_profit_pct(monthly_stats, num_months))
                total_won = ta_analysis.won.total if self.exists(ta_analysis, ['won', 'total']) else 0
                strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
                max_drawdown_pct = round(dd_analysis.max.drawdown, 2)
                max_drawdown_length = round(dd_analysis.max.len)
                num_winning_months = '{}'.format(self.get_num_winning_months(monthly_stats, num_months))
                profitfactor = round(ta_analysis.total.profitfactor, 3) if self.exists(ta_analysis, ['total', 'profitfactor']) else 0
                buyandhold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if self.exists(ta_analysis, ['total', 'buyandholdreturnpct']) else 0
                sqn_number = round(sqn_analysis.sqn, 2)
                monthlystatsprefix = ""
                equitycurvedata = ta_analysis.total.equity.equitycurvedata if self.exists(ta_analysis, ['total', 'equity', 'equitycurvedata']) else {}
                equitycurveangle = round(ta_analysis.total.equity.stats.angle) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'angle']) else 0
                equitycurveslope = round(ta_analysis.total.equity.stats.slope, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'slope']) else 0
                equitycurveintercept = round(ta_analysis.total.equity.stats.intercept, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'intercept']) else 0
                equitycurvervalue = round(ta_analysis.total.equity.stats.r_value, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'r_value']) else 0
                equitycurvepvalue = round(ta_analysis.total.equity.stats.p_value, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'p_value']) else 0
                equitycurvestderr = round(ta_analysis.total.equity.stats.std_err, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'std_err']) else 0

                model.get_backtest_model().add_result_row(strategy_id, exchange, symbol, timeframe, parameters, self.getdaterange(proc_daterange), startcash, self.getlotsize(args), total_closed,
                                     net_profit, net_profit_pct, avg_monthly_net_profit_pct, max_drawdown_pct, max_drawdown_length, strike_rate, num_winning_months,
                                     profitfactor, buyandhold_return_pct, sqn_number, monthlystatsprefix, monthly_stats, equitycurvedata, equitycurveangle, equitycurveslope,
                                     equitycurveintercept, equitycurvervalue, equitycurvepvalue, equitycurvestderr)
        return model

    def run_backtest_process(self, input_df, args):
        proc_daterange = self.get_processing_daterange(args.testdaterange)
        step3_model = Step3Model(input_df.reset_index(), proc_daterange["fromyear"], proc_daterange["frommonth"], proc_daterange["toyear"], proc_daterange["tomonth"], args.columnnameprefix)
        strat_list, exc_list, sym_list, tf_list = self.get_unique_index_value_lists(input_df)
        for strategy in strat_list:  # [strat_list[0]]:
            for exchange in exc_list:  # [exc_list[0]]:
                for symbol in sym_list:  # [sym_list[0]]:
                    for timeframe in tf_list:  # [tf_list[0]]:
                        candidates_data_df = input_df.loc[[(strategy, exchange, symbol, timeframe)]]

                        # Get list of candidates from Step2 for strategy/exchange/symbol/timeframe/date range
                        print("\n******** Processing {} rows for: {}, {}, {}, {}, {} ********".format(len(candidates_data_df), strategy, exchange, symbol, timeframe, args.testdaterange))

                        startcash = self.DEFAULT_STARTCASH_VALUE
                        runner = CerebroRunner()
                        self.init_cerebro(runner, args, startcash)

                        self._market_data_input_filename = self.get_marketdata_filename(exchange, symbol, timeframe)
                        self.check_market_data_csv_has_data(self._market_data_input_filename, proc_daterange)
                        self.add_data_to_cerebro(self._market_data_input_filename, proc_daterange)

                        strategy_enum = BTStrategyEnum.get_strategy_enum_by_str(strategy)
                        self.enqueue_strategies(candidates_data_df, strategy_enum, proc_daterange, args)

                        run_results = self.run_strategies(runner)

                        step3_model = self.append_model(step3_model, strategy, exchange, symbol, timeframe, run_results, args, proc_daterange)
        return step3_model

    def printfinalresultsheader(self, writer, step3_model):
        # Designate the rows
        h1 = step3_model.get_header_names()

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def printequitycurvedataheader(self, writer, step3_model):
        # Designate the rows
        h1 = step3_model.get_equitycurvedata_model().get_header_names()

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def printfinalresults(self, writer, model):
        print_list = model.get_model_data_arr()
        for item in print_list:
            writer.writerow(item)

    def printequitycurvedataresults(self, writer, model):
        print_list = model.get_equitycurvedata_model().get_model_data_arr()
        for item in print_list:
            writer.writerow(item)

    def cleanup(self):
        self._ofile1.close()
        self._ofile2.close()

    def run(self):
        args = self.parse_args()

        self._input_filename = self.get_input_filename(args)

        self._step2_df = self.read_csv_data(self._input_filename)

        self.init_output_files(args)

        self._step3_model = self.run_backtest_process(self._step2_df, args)

        self.printfinalresultsheader(self._writer1, self._step3_model)

        self.printequitycurvedataheader(self._writer2, self._step3_model)

        self.printfinalresults(self._writer1, self._step3_model)

        self.printequitycurvedataresults(self._writer2, self._step3_model)

        self.cleanup()

def main():
    step = BacktestingStep3()
    step.run()

if __name__ == '__main__':
    main()