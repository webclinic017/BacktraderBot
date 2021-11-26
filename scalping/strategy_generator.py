import argparse
import pandas as pd
import os
import io
from pathlib import Path
from scalping.strategy_generator_common import ShotStrategyGenerator, TemplateTokensVO
import random
import copy

FUTURES_MAKER_FEE_PCT = 0.02
FUTURES_TAKER_FEE_PCT = 0.04
SPOT_BNB_FEE_PCT = 0.075

DEFAULT_STRATEGY_TEMPLATE_ID = 1

MIN_TOTAL_SHOTS_COUNT = 0
MAX_MIN_TOTAL_SHOTS_PERCENTILE = 1

GRID_MODE_NONE = 0
GRID_MODE_1 = 1
GRID_MODE_2 = 2

CURRENT_GRID_MODE = GRID_MODE_NONE
GRID_MODE_ORDER_NUM = 3
GRID_MODE_1_DISTANCE_STEP_PCT = 0.02
GRID_MODE_2_SL_NEXT_ORDER_GAP_PCT = 0.02
GRID_MODE_2_IDEAL_TP_DISTANCE_RATIO = 0.33

IS_ADD_SMALL_RANDOM_VALUES_MODE = True
SMALL_RANDOM_VALUE_PCT = 15

FUTURE_MAX_STRATEGIES_NUM = 50
SPOT_MAX_STRATEGIES_NUM = 5

MT_FUTURE_ORDER_SIZE = 50
MT_SPOT_ORDER_SIZE = 11
MB_ORDER_SIZE = 0.0002

IS_SKIP_SHORT_STRATEGY_MODE = False

IS_FIXED_STRAT_PARAMS_MODE = True
FIXED_DISTANCE_VALUE_PCT = 0.9
FIXED_BUFFER_VALUE_PCT = 0.6
FIXED_TP_VALUE_PCT = 0.2
FIXED_SL_VALUE_PCT = 0.2

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

    def adjust_tokens_grid(self, is_moonbot, tokens_vo, grid_order_idx, grid_step_pct):
        tokens_vo_copy = copy.deepcopy(tokens_vo)
        adjust_distance_val = grid_order_idx * grid_step_pct
        if is_moonbot:
            tokens_vo_copy.mshot_price_min = round(tokens_vo_copy.mshot_price_min + adjust_distance_val, 2)
            tokens_vo_copy.mshot_price = round(tokens_vo_copy.mshot_price + adjust_distance_val, 2)
            if CURRENT_GRID_MODE == GRID_MODE_2 and grid_order_idx >= 1:
                tokens_vo_copy.tp = round(tokens_vo_copy.mshot_price * GRID_MODE_2_IDEAL_TP_DISTANCE_RATIO, 2)
        else:
            tokens_vo_copy.distance = round(tokens_vo_copy.distance + adjust_distance_val, 2)
            if CURRENT_GRID_MODE == GRID_MODE_2 and grid_order_idx >= 1:
                tokens_vo_copy.tp = round(tokens_vo_copy.distance * GRID_MODE_2_IDEAL_TP_DISTANCE_RATIO, 2)
        return tokens_vo_copy

    def get_trade_fees_pct(self, is_future):
        if is_future:
            return FUTURES_MAKER_FEE_PCT + FUTURES_TAKER_FEE_PCT
        else:
            return 2 * SPOT_BNB_FEE_PCT

    def get_order_size(self, is_moonbot, is_future):
        if is_moonbot:
            order_size = MB_ORDER_SIZE
        else:
            order_size = MT_SPOT_ORDER_SIZE if not is_future else MT_FUTURE_ORDER_SIZE

        return round(order_size)

    def get_order_size_mode_1(self, is_moonbot, is_future):
        order_size = self.get_order_size(is_moonbot, is_future)

        order_size = order_size / GRID_MODE_ORDER_NUM
        if IS_ADD_SMALL_RANDOM_VALUES_MODE:
            small_random_value = random.uniform(-SMALL_RANDOM_VALUE_PCT, SMALL_RANDOM_VALUE_PCT)
            order_size = order_size * (1 + small_random_value / 100)

        return round(order_size)

    def get_order_size_mode_2(self, is_moonbot, is_future, order_idx, tokens_vo_arr):
        order_size1 = self.get_order_size(is_moonbot, is_future)

        if order_idx == 0:
            return round(order_size1)

        tp1 = tokens_vo_arr[0].tp
        fees = self.get_trade_fees_pct(is_future)
        curr_order_size = order_size1
        prev_order_size = order_size1
        cum_sum_sl = 0
        cum_sum_loss = 0
        for i in range(1, order_idx + 1):
            prev_tokens_vo = tokens_vo_arr[i-1]
            curr_tokens_vo = tokens_vo_arr[i]
            cum_sum_sl += prev_tokens_vo.sl
            cum_sum_loss = cum_sum_loss + prev_order_size * (cum_sum_sl + fees) / 100
            curr_order_size = (1 + tp1 / 100) * cum_sum_loss / ((curr_tokens_vo.tp - fees) / 100)
            prev_order_size = curr_order_size
            cum_sum_sl += GRID_MODE_2_SL_NEXT_ORDER_GAP_PCT

        return round(curr_order_size)

    def get_tokens_vo(self, is_moonbot, pnl_row):
        tokens_vo = TemplateTokensVO.from_pnl_row(is_moonbot, pnl_row)

        if IS_FIXED_STRAT_PARAMS_MODE:
            if is_moonbot:
                tokens_vo.mshot_price_min = FIXED_DISTANCE_VALUE_PCT - 0.1
                tokens_vo.mshot_price = FIXED_DISTANCE_VALUE_PCT
            else:
                tokens_vo.distance = FIXED_DISTANCE_VALUE_PCT
                tokens_vo.buffer = FIXED_BUFFER_VALUE_PCT
            tokens_vo.tp = FIXED_TP_VALUE_PCT
            tokens_vo.sl = FIXED_SL_VALUE_PCT

        return tokens_vo

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

        strategy_template = self._strategy_generator.read_strategy_template(args.moonbot, DEFAULT_STRATEGY_TEMPLATE_ID)
        strategy_list = []
        for idx, pnl_row in shots_pnl_data_df.iterrows():
            tokens_vo = self.get_tokens_vo(is_moonbot, pnl_row)
            if IS_SKIP_SHORT_STRATEGY_MODE and tokens_vo.shot_type == "SHORT":
                continue

            if is_future and CURRENT_GRID_MODE == GRID_MODE_1:
                for grid_order_idx in range(GRID_MODE_ORDER_NUM):
                    tokens_vo_adj = self.adjust_tokens_grid(is_moonbot, tokens_vo, grid_order_idx, GRID_MODE_1_DISTANCE_STEP_PCT)
                    is_last = idx == shots_pnl_data_df.index[-1] and grid_order_idx == GRID_MODE_ORDER_NUM - 1
                    order_size = self.get_order_size_mode_1(is_moonbot, is_future)
                    strategy_list.append(self._strategy_generator.generate_strategy(is_moonbot, is_future, strategy_template, tokens_vo_adj, order_size, is_last))
            if is_future and CURRENT_GRID_MODE == GRID_MODE_2:
                max_real_shot_depth = pnl_row['max_real_shot_depth']
                distance_step_pct = (max_real_shot_depth - tokens_vo.distance) / (GRID_MODE_ORDER_NUM - 1)
                distance_step_pct = max(tokens_vo.sl + GRID_MODE_2_SL_NEXT_ORDER_GAP_PCT, distance_step_pct)
                token_vo_arr = []
                for grid_order_idx in range(GRID_MODE_ORDER_NUM):
                    tokens_vo_adj = self.adjust_tokens_grid(is_moonbot, tokens_vo, grid_order_idx, distance_step_pct)
                    token_vo_arr.append(tokens_vo_adj)
                    is_last = idx == shots_pnl_data_df.index[-1] and grid_order_idx == GRID_MODE_ORDER_NUM - 1
                    order_size = self.get_order_size_mode_2(is_moonbot, is_future, grid_order_idx, token_vo_arr)
                    strategy_list.append(self._strategy_generator.generate_strategy(is_moonbot, is_future, strategy_template, tokens_vo_adj, order_size, is_last))
            else:
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
