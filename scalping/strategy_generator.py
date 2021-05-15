import argparse
import pandas as pd
import os
import io
from pathlib import Path

MIN_TOTAL_SHOTS_COUNT = 0
MAX_MIN_TOTAL_SHOTS_PERCENTILE = 0.6
SPOT_MAX_STRATEGIES_NUM = 3

TOKEN001_STR = "{{TOKEN001}}"
TOKEN002_STR = "{{TOKEN002}}"
TOKEN003_STR = "{{TOKEN003}}"
TOKEN004_STR = "{{TOKEN004}}"
TOKEN005_STR = "{{TOKEN005}}"
TOKEN006_STR = "{{TOKEN006}}"
TOKEN007_STR = "{{TOKEN007}}"
TOKEN008_STR = "{{TOKEN008}}"
TOKEN009_STR = "{{TOKEN009}}"
TOKEN_STRATEGY_LIST_STR = "{{STRATEGY_LIST}}"

MT_STRATEGY_ID_START_FROM = 1617219803226

DEFAULT_OUTPUT_MB_FILENAME = "Binance-BTC-strat.txt"
DEFAULT_OUTPUT_MT_FILENAME = "algorithms.config"


class ShotStrategyGenerator(object):
    def __init__(self):
        pass

    def parse_args(self):
        parser = argparse.ArgumentParser(description='MB/MT shot strategies generator')

        parser.add_argument('-e', '--exchange',
                            type=str,
                            required=True,
                            help='The exchange name')

        parser.add_argument('-f', '--future',
                            action='store_true',
                            help=('Is instrument of future type?'))

        parser.add_argument('-b', '--moonbot',
                            action='store_true',
                            help=('Is MoonBot working mode? Otherwise it is MT mode.'))

        parser.add_argument('-t', '--mbordersize',
                            type=float,
                            required=True,
                            help='Default MB Moonshot strategy order size')

        parser.add_argument('-y', '--mtordersize',
                            type=float,
                            required=True,
                            help='Default MT Group Shot strategy order size')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_symbol_type_str(self, args):
        if args.future:
            return "future"
        else:
            return "spot"

    def get_app_suffix_str(self, args):
        if args.moonbot:
            return "mb"
        else:
            return "mt"

    def get_shots_pnl_filename(self, args):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        app_suffix_str = self.get_app_suffix_str(args)
        return '{}/../marketdata/shots/{}/{}/shots-best-pnl-{}-{}-{}.csv'.format(dirname, args.exchange, symbol_type_str, args.exchange, symbol_type_str, app_suffix_str)

    def get_template_filename(self, args):
        dirname = self.whereAmI()
        app_suffix_str = self.get_app_suffix_str(args)
        return '{}/templates/{}/tmpl.txt'.format(dirname, app_suffix_str)

    def get_strategy_template_filename(self, args):
        dirname = self.whereAmI()
        app_suffix_str = self.get_app_suffix_str(args)
        return '{}/templates/{}/strat_tmpl.txt'.format(dirname, app_suffix_str)

    def get_output_strategy_filename(self, args):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        if args.moonbot:
            return '{}/../marketdata/shots/{}/{}/{}_{}'.format(dirname, args.exchange, symbol_type_str, DEFAULT_OUTPUT_MB_FILENAME, symbol_type_str)
        else:
            return '{}/../marketdata/shots/{}/{}/{}_{}'.format(dirname, args.exchange, symbol_type_str, DEFAULT_OUTPUT_MT_FILENAME, symbol_type_str)

    def read_file(self, filename):
        return Path(filename).read_text()

    def write_file(self, filename, data):
        with io.open(filename, 'w', newline='\r\n') as f:
            f.write(data)

    def read_csv_data(self, filepath):
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            return None
        return df

    def filter_shots_pnl_rows(self, args, df):
        if not args.future:
            df = df[df['shot_type'] == 'LONG']

        df = df.sort_values(by=['total_shots_count'], ascending=False)

        df = df[df['total_shots_count'] >= MIN_TOTAL_SHOTS_COUNT]
        filter_val = int(round(len(df) * MAX_MIN_TOTAL_SHOTS_PERCENTILE))
        df = df.head(filter_val)

        if not args.future:
            df = df.head(SPOT_MAX_STRATEGIES_NUM)

        df = df.sort_values(by=['symbol_name', 'shot_type'], ascending=True)

        return df

    def get_tokens_map(self, args, index, pnl_row):
        symbol_name = pnl_row['symbol_name']
        symbol_type_str = self.get_symbol_type_str(args).upper()
        shot_type = pnl_row['shot_type']
        tp = pnl_row['TP']
        sl = pnl_row['SL']
        if args.moonbot:
            mshot_price_min = pnl_row['MShotPriceMin']
            mshot_price = pnl_row['MShotPrice']
            return {
                TOKEN001_STR: "Moonshot {} {} {}-{}-{}-{} {}".format(symbol_type_str, symbol_name, mshot_price_min, mshot_price, tp, sl, shot_type),
                TOKEN002_STR: symbol_name,
                TOKEN003_STR: "{:.4f}".format(tp),
                TOKEN004_STR: "{:.8f}".format(sl),
                TOKEN005_STR: "{:.4f}".format(mshot_price_min),
                TOKEN006_STR: "{:.4f}".format(mshot_price),
                TOKEN007_STR: "{}".format(args.mbordersize)
            }
        else:
            distance = pnl_row['Distance']
            buffer = pnl_row['Buffer']
            return {
                TOKEN001_STR: "{}".format(MT_STRATEGY_ID_START_FROM + index),
                TOKEN002_STR: "Shot {} {} {}-{}-{}-{} {}".format(symbol_type_str, symbol_name, distance, buffer, tp, sl, shot_type),
                TOKEN003_STR: symbol_name,
                TOKEN004_STR: "{}".format(distance),
                TOKEN005_STR: "{}".format(buffer),
                TOKEN006_STR: "{}".format(1 if shot_type == "LONG" else -1 if shot_type == "SHORT" else ""),
                TOKEN007_STR: "{}".format(args.mtordersize),
                TOKEN008_STR: "{}".format(tp),
                TOKEN009_STR: "{}".format(sl)
            }

    def get_template_token_map(self, strategy_list_str):
        return {
            TOKEN_STRATEGY_LIST_STR: strategy_list_str
        }

    def apply_template_tokens(self, strategy_template, tokens_map):
        s = strategy_template
        for token, value in tokens_map.items():
            s = s.replace(token, value)
        return s

    def append_divider(self, args, strategy_str, is_last):
        if not args.moonbot:
            if not is_last:
                divider = ",\n"
            else:
                divider = ""
            strategy_str = strategy_str + divider
        return strategy_str

    def run(self):
        args = self.parse_args()

        filename = self.get_shots_pnl_filename(args)
        shots_pnl_data_df = self.read_csv_data(filename)
        if shots_pnl_data_df is None or shots_pnl_data_df.empty:
            print("*** No shots PnL data found! Exiting.")
            exit(-1)

        shots_pnl_data_df = self.filter_shots_pnl_rows(args, shots_pnl_data_df)
        if shots_pnl_data_df is None or shots_pnl_data_df.empty:
            print("*** No shots PnL data after applying filter! Exiting.")
            exit(-1)

        strategy_template = self.read_file(self.get_strategy_template_filename(args))
        strategy_list = []
        for idx, pnl_row in shots_pnl_data_df.iterrows():
            tokens_map = self.get_tokens_map(args, idx, pnl_row)
            strategy_str = self.apply_template_tokens(strategy_template, tokens_map)
            strategy_str = self.append_divider(args, strategy_str, idx == shots_pnl_data_df.index[-1])
            strategy_list.append(strategy_str)
        strategy_list_str = ''.join(strategy_list)

        template = self.read_file(self.get_template_filename(args))
        all_strategies_str = self.apply_template_tokens(template, self.get_template_token_map(strategy_list_str))

        out_filename = self.get_output_strategy_filename(args)
        self.write_file(out_filename, all_strategies_str)
        print("\nStrategy file {} has been generated!".format(out_filename))


def main():
    step = ShotStrategyGenerator()
    step.run()


if __name__ == '__main__':
    main()
