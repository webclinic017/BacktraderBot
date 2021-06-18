import argparse
import pandas as pd
import numpy as np
import os
import random

MODE1_PRINT_BLACKLIST = 1
MODE2_GENERATE_MULTIPLE_STRATEGIES_FOR_WHITELIST = 2

DEFAULT_WORKING_PATH = "/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies"
DEFAULT_OUTPUT_MB_FILENAME = "Binance-BTC-strat.txt"
DEFAULT_OUTPUT_MT_FILENAME = "algorithms.config"

MAX_SLIPPAGE_PCT=0.1
DEEP_LOSS_COUNT_THRESHOLD=1


class TemplateTokensVO(object):
    def __init__(self, is_moonbot, pnl_row):
        self.symbol_name = pnl_row['symbol_name']
        self.shot_type = pnl_row['shot_type']
        self.tp = pnl_row['TP']
        self.sl = pnl_row['SL']
        if is_moonbot:
            self.mshot_price_min = pnl_row['MShotPriceMin']
            self.mshot_price = pnl_row['MShotPrice']
        else:
            self.distance = pnl_row['Distance']
            self.buffer = pnl_row['Buffer']


class TMMExcelReportAnalyzer(object):
    def __init__(self):
        pass

    def parse_args(self):
        parser = argparse.ArgumentParser(description='TraderMake Money Excel report analyzer')

        parser.add_argument('-m', '--mode',
                            type=int,
                            required=True,
                            help=('Script working mode'))

        parser.add_argument('-b', '--moonbot',
                            action='store_true',
                            help=('Is MoonBot working mode? Otherwise it is MT mode.'))

        parser.add_argument('-l', '--def_leverage',
                            type=float,
                            required=True,
                            help=('Default leverage'))

        parser.add_argument('-s', '--def_sl_pct',
                            type=float,
                            required=True,
                            help=('Default SL, %'))

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_report_filename(self):
        return '{}/report.xlsx'.format(DEFAULT_WORKING_PATH)

    def get_output_strategy_filename(self, args):
        if args.moonbot:
            return '{}/{}'.format(DEFAULT_WORKING_PATH, DEFAULT_OUTPUT_MB_FILENAME)
        else:
            return '{}/{}'.format(DEFAULT_WORKING_PATH, DEFAULT_OUTPUT_MT_FILENAME)

    def read_report_data(self, filepath):
        try:
            df = pd.read_excel(filepath, sheet_name='Worksheet', engine='openpyxl', skiprows=7, keep_default_na=False, usecols="A:N", convert_float=False, header=None,
                               dtype={'D': np.float64, 'F': np.float64, 'I': np.float64, 'J': np.float64, 'K': np.float64, 'L': np.float64, 'M': np.float64, 'N': np.float64})
            df = df.rename(columns={0: "symbol", 1: "category", 2: "entry_timestamp", 3: "avg_entry_price", 4: "exit_timestamp", 5: "avg_exit_price", 6: "duration", 7: "side", 8: "pnl_pct", 9: "pnl_usdt", 10: "net_pnl_usdt", 11: "volume", 12: "volume_usdt", 13: "fees_usdt"})
        except Exception as e:
            return None
        return df

    def process_mode1(self, args, report_data_df):
        data_long_df = report_data_df[report_data_df['side'] == "LONG"]
        symbol_list = data_long_df['symbol'].unique()
        l_data = {}
        for symbol in symbol_list:


    def process_mode2(self, args, report_data_df):
        None


    def run(self):
        random.seed()
        args = self.parse_args()

        if args.mode not in [MODE1_PRINT_BLACKLIST, MODE2_GENERATE_MULTIPLE_STRATEGIES_FOR_WHITELIST]:
            print("Please provide a valid working mode: -m {}".format([MODE1_PRINT_BLACKLIST, MODE2_GENERATE_MULTIPLE_STRATEGIES_FOR_WHITELIST]))
            exit(-2)

        filename = self.get_report_filename()
        report_data_df = self.read_report_data(filename)
        if report_data_df is None or report_data_df.empty:
            print("*** No TraderMake Money Excel report data found! Exiting.")
            exit(-1)

        if args.mode == MODE1_PRINT_BLACKLIST:
            self.process_mode1(args, report_data_df)
        elif args.mode == MODE2_GENERATE_MULTIPLE_STRATEGIES_FOR_WHITELIST:
            self.process_mode2(args, report_data_df)


def main():
    step = TMMExcelReportAnalyzer()
    step.run()


if __name__ == '__main__':
    main()
