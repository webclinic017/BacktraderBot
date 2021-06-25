import argparse
import pandas as pd
import os
import io
from pathlib import Path
from strategy_generator_common import ShotStrategyGenerator, TemplateTokensVO
import random

MIN_TOTAL_SHOTS_COUNT = 0
MAX_MIN_TOTAL_SHOTS_PERCENTILE = 1

FUTURE_MAX_STRATEGIES_NUM = 30
SPOT_MAX_STRATEGIES_NUM = 10

IS_GRID_MODE_ENABLED_FLAG = False
GRID_MODE_ORDER_NUM = 3
GRID_MODE_DISTANCE_STEP_PCT = 0.03
IS_ADD_SMALL_RANDOM_VALUES_MODE = True
SMALL_RANDOM_VALUE_PCT = 15

MT_FUTURE_ORDER_SIZE = 300
MT_SPOT_ORDER_SIZE = 85
MB_ORDER_SIZE = 0.0002

DEFAULT_OUTPUT_MB_FILENAME = "Binance-BTC-strat.txt"
DEFAULT_OUTPUT_MT_FILENAME = "algorithms.config"


class StrategyGeneratorHandler(object):
    def __init__(self):
        self._strategy_generator = ShotStrategyGenerator()

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

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_symbol_type_str(self, is_future):
        if is_future:
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
        symbol_type_str = self.get_symbol_type_str(args.future)
        app_suffix_str = self.get_app_suffix_str(args)
        return '{}/../marketdata/shots/{}/{}/shots-best-pnl-{}-{}-{}.csv'.format(dirname, args.exchange, symbol_type_str, args.exchange, symbol_type_str, app_suffix_str)

    def get_output_strategy_filename(self, args):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args.future)
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
        else:
            df = df.head(FUTURE_MAX_STRATEGIES_NUM)

        df = df.sort_values(by=['symbol_name', 'shot_type'], ascending=True)

        return df

    def get_order_size(self, is_moonbot, is_future):
        if is_moonbot:
            order_size = MB_ORDER_SIZE
        else:
            order_size = MT_SPOT_ORDER_SIZE if not is_future else MT_FUTURE_ORDER_SIZE

        if is_future and IS_GRID_MODE_ENABLED_FLAG:
            order_size = order_size / GRID_MODE_ORDER_NUM
            if IS_ADD_SMALL_RANDOM_VALUES_MODE:
                small_random_value = random.uniform(-SMALL_RANDOM_VALUE_PCT, SMALL_RANDOM_VALUE_PCT)
                order_size = order_size * (1 + small_random_value / 100)

        return round(order_size)

    def run(self):
        random.seed()
        args = self.parse_args()
        is_moonbot = args.moonbot
        is_future = args.future

        filename = self.get_shots_pnl_filename(args)
        shots_pnl_data_df = self.read_csv_data(filename)
        if shots_pnl_data_df is None or shots_pnl_data_df.empty:
            print("*** No shots PnL data found! Exiting.")
            exit(-1)

        shots_pnl_data_df = self.filter_shots_pnl_rows(args, shots_pnl_data_df)
        if shots_pnl_data_df is None or shots_pnl_data_df.empty:
            print("*** No shots PnL data after applying filter! Exiting.")
            exit(-1)

        strategy_template = self._strategy_generator.read_strategy_template(args.moonbot)
        strategy_list = []
        for idx, pnl_row in shots_pnl_data_df.iterrows():
            if is_future and IS_GRID_MODE_ENABLED_FLAG:
                for grid_order_idx in range(GRID_MODE_ORDER_NUM):
                    tokens_vo = TemplateTokensVO.from_pnl_row(is_moonbot, pnl_row)
                    tokens_vo = self._strategy_generator.adjust_tokens_grid(is_moonbot, tokens_vo, grid_order_idx, GRID_MODE_DISTANCE_STEP_PCT)
                    is_last = idx == shots_pnl_data_df.index[-1] and grid_order_idx == GRID_MODE_ORDER_NUM - 1
                    order_size = self.get_order_size(is_moonbot, is_future)
                    strategy_list.append(self._strategy_generator.generate_strategy(is_moonbot, is_future, strategy_template, tokens_vo, order_size, is_last))
            else:
                tokens_vo = TemplateTokensVO.from_pnl_row(is_moonbot, pnl_row)
                is_last = idx == shots_pnl_data_df.index[-1]
                order_size = self.get_order_size(is_moonbot, is_future)
                strategy_list.append(self._strategy_generator.generate_strategy(is_moonbot, is_future, strategy_template, tokens_vo, order_size, is_last))
        strategy_list_str = ''.join(strategy_list)

        final_content = self._strategy_generator.generate_final_content(strategy_list_str, is_moonbot, is_future)
        out_filename = self.get_output_strategy_filename(args)
        self.write_file(out_filename, final_content)

        print("\nStrategy file {} has been generated!".format(out_filename))


def main():
    step = StrategyGeneratorHandler()
    step.run()


if __name__ == '__main__':
    main()
