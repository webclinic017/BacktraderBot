

import argparse

from datetime import datetime
from config.strategy_config import AppConfig
import os
import csv
import pandas as pd
import itertools as it

class BT2MT4MarketDataConverter(object):

    _ENABLE_FILTERING = AppConfig.is_global_step1_enable_filtering()

    def __init__(self):
        self._market_data_input_filename = None
        self.input_data_df = None
        self._output_file1_full_name = None
        self._ofile1 = None
        self._writer1 = None
        self._backtest_model = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtradter to MT4 Market Data Converter')

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

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_input_filename(self, args):
        return './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(args.exchange, args.symbol, args.timeframe, args.exchange, args.symbol, args.timeframe)

    def get_output_path(self, base_dir):
        return '{}'.format(base_dir)

    def get_output_filename1(self, base_path, args):
        return '{}/MT4-{}-{}-{}.csv'.format(base_path, args.exchange, args.symbol, args.timeframe)

    def init_output_files(self, args):
        base_dir = self.whereAmI()
        output_path = self.get_output_path(base_dir)
        self._output_file1_full_name = self.get_output_filename1(output_path, args)

        self._ofile1 = open(self._output_file1_full_name, "w")
        self._writer1 = csv.writer(self._ofile1, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONE)

    def read_csv_data(self, filepath):
        df = pd.read_csv(filepath)
        return df

    def convert(self, input_df):
        result = []
        counter = it.count()
        for index, row in input_df.iterrows():
            cnt = next(counter)
            if cnt % 10000 == 0:
                print("Processing row: {}".format(cnt))

            # Input format:
            # Timestamp, Open, High, Low, Close, Volume
            timestamp_str = row["Timestamp"]
            open = row["Open"]
            high = row["High"]
            low = row["Low"]
            close = row["Close"]
            volume = row["Volume"]

            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
            datetime_str = timestamp.strftime("%Y.%m.%d %H:%M:%S")
            volume_int = int(volume)
            # Output format:
            # "Date", "Open", "High", "Low", "Close", "Tick Volume", "Volume", "Spread"
            result.append([datetime_str, open, high, low, close, volume_int, volume_int, 1])

        return result

    def printfinalresultsheader(self, writer):
        # Designate the rows
        h1 = ["Date", "Open", "High", "Low", "Close", "Tick Volume", "Volume", "Spread"]

        # Print header
        print_list = [h1]
        for row in print_list:
            writer.writerow(row)

    def printfinalresults(self, writer, data_arr):
        print_list = data_arr
        print("Writing {} rows...".format(len(print_list)))
        for item in print_list:
            writer.writerow(item)

    def cleanup(self):
        self._ofile1.close()

    def run(self):
        args = self.parse_args()

        self._market_data_input_filename = self.get_input_filename(args)

        self.init_output_files(args)

        print("Processing the market data file: {}".format(self._market_data_input_filename))

        self.input_data_df = self.read_csv_data(self._market_data_input_filename)

        print("Converting market data to MT4 format into file: {}".format(self._output_file1_full_name))

        result = self.convert(self.input_data_df)

        self.printfinalresultsheader(self._writer1)

        print("Writing conversion results into file: {}".format(self._output_file1_full_name))

        self.printfinalresults(self._writer1, result)

        self.cleanup()


def main():
    step = BT2MT4MarketDataConverter()
    step.run()


if __name__ == '__main__':
    main()