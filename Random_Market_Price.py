import backtrader as bt
import backtrader.feeds as btfeeds
from datetime import timedelta
import argparse
from decimal import Decimal
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from extensions.sizers.cashsizer import FixedCashSizer
from config.strategy_config import AppConfig
from config.strategy_enum import BTStrategyEnum
from plotting.equity_curve import EquityCurvePlotter
from model.backtestmodel import BacktestModel
from model.backtestmodelgenerator import BacktestModelGenerator
from strategies.helper.utils import Utils
from datetime import datetime
import pandas as pd
from random import random
from random import seed
import time
import os
import csv

IS_RENDER_PRICE_GRAPH_IMAGE = False

STEP_NAME = "Test01"
INITIAL_PRICE = 10000
AVG_BODY_SIZE_PCT = 0.0005
TICK_SIZE = 0.5

tradesopen = {}
tradesclosed = {}

RANDOM_DATA_CSV_HEADER = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']


class RandomMarketPrice(object):

    _INDEX_COLUMNS = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters']

    def __init__(self):
        self._file_index = None
        self._exchange = None
        self._currency_pair = None
        self._timeframe = None
        self._startcash = None
        self._lotsize = None
        self._lottype = None
        self._cerebro = None
        self._strategy_enum = None
        self._params = dict()
        self._equity_curve_plotter = EquityCurvePlotter(STEP_NAME)
        self._is_output_file1_exists = None
        self._output_file1_full_name = None
        self._ofile1 = None
        self._writer1 = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='RandomMarketPrice')

        parser.add_argument('-r', '--runid',
                            type=str,
                            default="Test01RandomMarketPrice",
                            help='Run ID')

        parser.add_argument('-y', '--strategy',
                            type=str,
                            required=True,
                            help='The strategy ID')

        parser.add_argument('-f', '--file_index',
                            type=int,
                            required=True,
                            help='File Index')

        parser.add_argument('--commtype',
                            default="Percentage",
                            type=str,
                            choices=["Percentage", "Fixed"],
                            help='The type of commission to apply to a trade')

        parser.add_argument('--commission',
                            default=0.00025,
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Debug logs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_random_market_data_filename(self, symbol, timeframe, file_index):
        return './marketdata/random/{}/{}/random-{}-{}-{:03d}.csv'.format(symbol, timeframe, symbol, timeframe, file_index)

    def get_randomdata_price_image_basedir(self, args):
        return './strategyrun_results/{}/{}_PriceImages'.format(args.runid, STEP_NAME)

    def get_randomdata_price_image_filename(self, basedir, file_index, exchange, symbol, timeframe):
        return '{}/{:03d}-random-{}-{}-{}.png'.format(basedir, file_index, exchange, symbol, timeframe)

    def check_outputfile_exists(self):
        return os.path.exists(self._output_file1_full_name)

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_filename1(self, base_path, args):
        return '{}/{}_Result.csv'.format(base_path, args.runid)

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

    def init_cerebro(self, args, startcash, lotsize, lottype):
        # Create an instance of cerebro
        self._cerebro = bt.Cerebro()

        # Set our desired cash start
        self._cerebro.broker.setcash(startcash)

        # Add the analyzers we are interested in
        self._cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self._cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd", initial_cash=startcash)
        self._cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=startcash)

        # add the sizer
        if lottype != "" and lottype == "Percentage":
            self._cerebro.addsizer(VariablePercentSizer, percents=lotsize, debug=args.debug)
        else:
            self._cerebro.addsizer(FixedCashSizer, cashamount=lotsize, commission=args.commission)

        if args.commtype.lower() == 'percentage':
            self._cerebro.broker.setcommission(args.commission)

    def get_strategy_enum(self, args):
        return BTStrategyEnum.get_strategy_enum_by_str(args.strategy)

    def init_params(self, strategy_enum, args):
        debug_strategy_config = AppConfig.get_default_strategy_params(strategy_enum)
        base_params = debug_strategy_config[0]
        params_dict = debug_strategy_config[1]
        self._file_index = args.file_index
        self._exchange = base_params["exchange"]
        self._currency_pair = base_params["currency_pair"]
        self._timeframe = base_params["timeframe"]
        self._startcash = base_params["startcash"]
        self._lotsize = base_params["lotsize"]
        self._lottype = base_params["lottype"]
        self._params = params_dict.copy()
        self._params.update(
            {
                ("debug", args.debug),
                ("startcash", self._startcash)
            }
        )

    def add_strategy(self):
        strategy_class = self._strategy_enum.value.clazz
        self._cerebro.addstrategy(strategy_class, **self._params)

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

    def add_datas(self, args):
        fromdate = self.get_fromdate(self._params)
        todate = self.get_todate(self._params)
        timeframe = self._timeframe
        file_index = self._file_index

        data = self.build_random_data(args, fromdate, todate, timeframe, file_index)

        # Add the data to Cerebro
        self._cerebro.adddata(data, "data_1m")

    def toNearest(self, num, tickSize):
        if tickSize > 0:
            tickDec = Decimal(str(tickSize))
            return float((Decimal(round(num / tickSize, 0)) * tickDec))
        else:
            return int(num)

    def generate_random_walk_arr(self, initial_price, num_entries, avg_body_size_pct, index, tickSize):
        random_walk_arr = list()
        random_walk_arr.append(initial_price)

        avg_body_size = initial_price * avg_body_size_pct
        seed(int(round(time.time() * 1000 + index)))
        for i in range(1, num_entries):
            rnd = random() - 0.5
            movement = 2 * avg_body_size * rnd
            value = self.toNearest(random_walk_arr[i - 1] + movement, tickSize)
            random_walk_arr.append(value)
        return random_walk_arr

    def generate_random_data_df(self, index, fromdate, todate):
        csv_data = []
        time_step = timedelta(minutes=1)
        num_entries = int((todate - fromdate).total_seconds() / 60) + 1
        random_data_arr = self.generate_random_walk_arr(INITIAL_PRICE, num_entries, AVG_BODY_SIZE_PCT, index, TICK_SIZE)
        tstamp = fromdate
        for i in range(1, num_entries):
            open = random_data_arr[i-1]
            close = random_data_arr[i]
            high = max(open, close)
            low = min(open, close)
            ohlc = [tstamp.strftime("%Y-%m-%dT%H:%M:%S"), open, high, low, close, 0]
            csv_data.append(ohlc)
            tstamp = tstamp + time_step
        df = pd.DataFrame(csv_data, columns=RANDOM_DATA_CSV_HEADER).set_index('Timestamp')
        return df

    def build_random_data(self, args, fromdate, todate, timeframe, file_index):
        fromdate_back_delta = timedelta(days=1)  # Adjust from date to add more candle data from the past to strategy to prevent any calculation problems with indicators
        granularity = Utils.get_granularity_by_tf_str(timeframe)
        timeframe_id = granularity[0][0]
        compression = granularity[0][1]
        fromdate_back = fromdate - fromdate_back_delta
        todate_delta = timedelta(days=1)  # Adjust to date to add more candle data
        todate_beyond = todate + todate_delta

        random_market_data_filename = self.get_random_market_data_filename(self._currency_pair, timeframe, file_index)
        data_df = self.generate_random_data_df(file_index, fromdate_back, todate_beyond)
        data_df.to_csv(random_market_data_filename)
        if IS_RENDER_PRICE_GRAPH_IMAGE:
            price_data_arr = data_df['Close'].values.tolist()
            self.render_price_image(args, file_index, price_data_arr)

        return btfeeds.GenericCSVData(
            dataname=random_market_data_filename,
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

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def getdaterange(self, arr):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(arr["fromyear"], arr["frommonth"], arr["fromday"], arr["toyear"], arr["tomonth"], arr["today"])

    def create_model(self, run_results, args):
        debug_params = self._params
        model = BacktestModel(debug_params["fromyear"], debug_params["frommonth"], debug_params["toyear"], debug_params["tomonth"])
        generator = BacktestModelGenerator(False)
        generator.populate_model_data(model, run_results, args.strategy, self._exchange, self._currency_pair, self._timeframe, args, self._lotsize, self._lottype, self.getdaterange(debug_params))
        return model

    def render_price_image(self, args, file_index, price_data_arr):
        basedir = self.get_randomdata_price_image_basedir(args)
        os.makedirs(basedir, exist_ok=True)
        output_filename = self.get_randomdata_price_image_filename(basedir, file_index, self._exchange, self._currency_pair, self._timeframe)
        self._equity_curve_plotter.generate_generic_data_image(output_filename, price_data_arr)

    def printfinalresultsheader(self, writer, model):
        if self._is_output_file1_exists is True:
            return

        # Designate the rows
        h1 = model.get_header_names()

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

    def run(self):
        args = self.parse_args()

        self._strategy_enum = self.get_strategy_enum(args)
        self.init_params(self._strategy_enum, args)

        self.init_cerebro(args, self._startcash, self._lotsize, self._lottype)

        self.add_strategy()

        self.add_datas(args)

        self.init_output_files(args)

        # Run the strategy
        strategies = self._cerebro.run()

        bktest_model = self.create_model([strategies], args)
        # self.render_equity_curve_image(bktest_model, args)

        self.printfinalresultsheader(self._writer1, bktest_model)

        self.printfinalresults(self._writer1, bktest_model.get_model_data_arr())


def main():
    strat = RandomMarketPrice()
    strat.run()


if __name__ == '__main__':
    main()

