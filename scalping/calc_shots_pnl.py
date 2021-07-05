import argparse
import pandas as pd
import numpy as np
import os
import itertools
import collections
import csv

string_types = str

COMMISSIONS_PCT = 0.02 + 0.04
SLIPPAGE_PCT = 0.02

TOP_DISTANCE_VALUE_PERCENTILE = 0.2

IS_ADJUST_DISTANCE_IN_ULTRASHORT_MODE = False
MIN_PRACTICAL_DISTANCE = 0.5
MAX_PRACTICAL_DISTANCE = 3.0

MIN_TP_PCT_SPOT = 0.26
MIN_TP_PCT_FUTURE = 0.12
DEFAULT_MIN_STEP = 0.02
TRIAL_STEP_PCT = 0.02

MIN_SL_PCT = 0.35
MAX_SL_PCT = 0.41

FUTURE_MIN_RR_RATIO = 2
SPOT_TP_TO_DISTANCE_RATIO_MIN = 0.3
SPOT_TP_TO_DISTANCE_RATIO_MAX = 0.4

MAX_TP_TO_SHOT_RATIO = 0.5
CREATE_PNL_FILE_FLAG = True

MIN_TP_COUNT_GROUPS_THRESHOLD = 1


class ShotsPnlCalculator(object):
    def __init__(self):
        self._shotsdata_filename = None
        self._shots_data_df = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Shots PnL Calculator')

        parser.add_argument('-u', '--ultrashortmode',
                            action='store_true',
                            help=('Ultra-short mode flag'))

        parser.add_argument('-e', '--exchange',
                            type=str,
                            required=True,
                            help='The exchange name')

        parser.add_argument('-s', '--symbol',
                            type=str,
                            required=True,
                            help='Instrument/Currency Pair')

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

    def get_symbol_type_str(self, args):
        if args.future:
            return "future"
        else:
            return "spot"

    def get_shotsdata_filename(self, args):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        return '{}/../marketdata/shots/{}/{}/shots-{}-{}.csv'.format(dirname, args.exchange, symbol_type_str, args.exchange, symbol_type_str)

    def read_csv_data(self, filepath):
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            return None
        return df

    def write_pnl_data_to_file(self, args, df, shot_type):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        os.makedirs(output_path, exist_ok=True)

        # Save it
        suffix = "mb" if args.moonbot else "mt"
        filename = '{}/shots-pnl-{}-{}-{}-{}-{}.csv'.format(output_path, args.exchange, symbol_type_str, args.symbol, shot_type, suffix)
        df.to_csv(filename)

    def write_best_pnl_rows_to_file(self, args, total_shots_count, df, shot_type):
        # Save it
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        os.makedirs(output_path, exist_ok=True)

        if args.moonbot:
            header = ['symbol_name', 'shot_type', 'total_shots_count', 'MShotPriceMin', 'MShotPrice', 'TP', 'SL']
        else:
            header = ['symbol_name', 'shot_type', 'total_shots_count', 'Distance', 'Buffer', 'TP', 'SL']

        csv_rows = []
        for index, row in df.iterrows():
            csv_rows.append([
                                args.symbol,
                                shot_type,
                                total_shots_count,
                                row['MShotPriceMin'] if args.moonbot else row['Distance'],
                                row['MShotPrice'] if args.moonbot else row['Buffer'],
                                row['TP'],
                                row['SL']
                             ])

        suffix = "mb" if args.moonbot else "mt"
        filename = '{}/shots-best-pnl-{}-{}-{}.csv'.format(output_path, args.exchange, symbol_type_str, suffix)

        file_exists = False
        if os.path.exists(filename):
            file_exists = True

        ofile = open(filename, "a")
        writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        if not file_exists:
            # Print header
            print_list = [header]
            for row in print_list:
                writer.writerow(row)

        print_list = []
        print_list.extend(csv_rows)
        print("Writing {} rows...".format(len(print_list)))
        for item in print_list:
            writer.writerow(item)
        ofile.flush()
        ofile.close()

    def sort_best_pnl_file_rows(self, args):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        suffix = "mb" if args.moonbot else "mt"
        filename = '{}/shots-best-pnl-{}-{}-{}.csv'.format(output_path, args.exchange, symbol_type_str, suffix)

        best_pnl_df = self.read_csv_data(filename)
        if best_pnl_df is None or best_pnl_df.empty:
            return

        best_pnl_df = best_pnl_df.set_index('symbol_name')
        best_pnl_df = best_pnl_df.sort_values(by=['total_shots_count'], ascending=False)
        best_pnl_df.to_csv(filename)

    def get_simulation_params(self, is_ultrashort, is_moonbot, is_future, shot_depth_list, shot_count_list):
        non_zero_idx = [i for i, item in enumerate(shot_count_list) if item != 0][-1]
        min_s = shot_depth_list[0]
        max_s = shot_depth_list[non_zero_idx]
        min_tp_pct = MIN_TP_PCT_FUTURE if is_future else MIN_TP_PCT_SPOT
        min_distance = min_s
        max_distance = max_s + DEFAULT_MIN_STEP

        if is_moonbot:
            return {
                "MShotPriceMin": np.arange(min_distance, max_distance - 0.1, DEFAULT_MIN_STEP),
                "MShotPrice": np.arange(min_distance, max_distance, DEFAULT_MIN_STEP),
                "tp": np.arange(min_tp_pct, (max_s + 0.2 / 2) * MAX_TP_TO_SHOT_RATIO + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP),
                "sl": np.arange(MIN_SL_PCT, MAX_SL_PCT, DEFAULT_MIN_STEP)
            }
        else:
            return {
                "distance": np.arange(min_distance, max_distance, DEFAULT_MIN_STEP),
                "buffer": 0.2,
                "tp": 0.12,
                "sl": 1.2
            }

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

    def get_sim_combinations(self, is_ultrashort, is_moonbot, is_future, shot_depth_list, shot_count_list):
        simulation_params = self.get_simulation_params(is_ultrashort, is_moonbot, is_future, shot_depth_list, shot_count_list)
        kwargz = simulation_params
        optkeys = list(simulation_params)
        vals = self.iterize(kwargz.values())
        optvals = itertools.product(*vals)
        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)
        optkwargs = map(dict, okwargs1)
        return list(optkwargs)

    def round_base(self, x, base, prec):
        return round(base * round(float(x)/base), prec)

    def pct_val(self, val, total, base):
        return self.round_base(100 * val / total, base, 0)

    def calculate_optimal_distance(self, shot_depth_list, shot_count_list):
        # Calculate best distance for a group of shots: weighted average
        return np.average(shot_depth_list, weights=shot_count_list)

    def simulate_shots(self, is_ultrashort, is_moonbot, is_future, groups_df):
        arr_out = []

        shot_depth_list = list(groups_df["shot_depth"].values)
        shot_count_list = list(groups_df["counts"].values)

        combinations = self.get_sim_combinations(is_ultrashort, is_moonbot, is_future, shot_depth_list, shot_count_list)
        for c_idx, c_dict in enumerate(combinations):
            if c_idx % 100 == 0:
                print("{}/{}".format(c_idx, len(combinations)))
            c_tp = c_dict["tp"]
            c_sl = c_dict["sl"]
            if is_moonbot:
                c_mshot_price_min = c_dict["MShotPriceMin"]
                c_mshot_price = c_dict["MShotPrice"]
                if c_mshot_price <= c_mshot_price_min:
                    continue
                if c_tp > (c_mshot_price / MAX_TP_TO_SHOT_RATIO):
                    continue
                if is_future:
                    if c_sl / c_tp < FUTURE_MIN_RR_RATIO:
                        continue
                else:
                    tp_to_distance_ratio = c_tp / c_mshot_price_min
                    if tp_to_distance_ratio < SPOT_TP_TO_DISTANCE_RATIO_MIN or tp_to_distance_ratio > SPOT_TP_TO_DISTANCE_RATIO_MAX:
                        continue
                comb_params_arr = [c_mshot_price_min, c_mshot_price, c_tp, c_sl]
            else:
                c_distance = c_dict["distance"]
                c_buffer = c_dict["buffer"]
                if c_distance <= c_buffer / 2:
                    continue
                if c_tp > ((c_distance + c_buffer / 2) / MAX_TP_TO_SHOT_RATIO):
                    continue
                if is_future:
                    if c_sl / c_tp < FUTURE_MIN_RR_RATIO:
                        continue
                else:
                    tp_to_distance_ratio = c_tp / c_distance
                    if tp_to_distance_ratio < SPOT_TP_TO_DISTANCE_RATIO_MIN or tp_to_distance_ratio > SPOT_TP_TO_DISTANCE_RATIO_MAX:
                        continue
                comb_params_arr = [c_distance, c_buffer, c_tp, c_sl]

            optimal_distance = self.calculate_optimal_distance(shot_depth_list, shot_count_list)
            if is_moonbot:
                arr = [round(comb_params_arr[0], 2),
                       round(optimal_distance, 2),
                       round(c_tp, 2),
                       round(c_sl, 2)
                ]
            else:
                arr = [round(optimal_distance, 2),
                       round(comb_params_arr[1], 2),
                       round(c_tp, 2),
                       round(c_sl, 2)
                ]
            arr_out.append(arr)

        if is_moonbot:
            df = pd.DataFrame(arr_out, columns=['MShotPriceMin', 'MShotPrice', 'TP', 'SL'])
            df = df.sort_values(by=['MShotPrice'], ascending=True)
        else:
            df = pd.DataFrame(arr_out, columns=['Distance', 'Buffer', 'TP', 'SL'])
            df = df.sort_values(by=['Distance'], ascending=True)
        return df

    def get_best_pnl_rows(self, df):
        return df.head(1)

    def adjust_distance(self, is_ultrashort, is_moonbot, df):
        if is_ultrashort and IS_ADJUST_DISTANCE_IN_ULTRASHORT_MODE:
            df_copy = df.copy()
            for idx, row in df_copy.iterrows():
                if is_moonbot:
                    if row['MShotPrice'] < MIN_PRACTICAL_DISTANCE:
                        df.loc[idx, 'MShotPrice'] = MIN_PRACTICAL_DISTANCE
                        df.loc[idx, 'MShotPriceMin'] = MIN_PRACTICAL_DISTANCE - 0.1
                    elif row['MShotPrice'] > MAX_PRACTICAL_DISTANCE:
                        df.loc[idx, 'MShotPrice'] = MAX_PRACTICAL_DISTANCE
                        df.loc[idx, 'MShotPriceMin'] = MAX_PRACTICAL_DISTANCE - 0.1
                else:
                    if row['Distance'] < MIN_PRACTICAL_DISTANCE:
                        df.loc[idx, 'Distance'] = MIN_PRACTICAL_DISTANCE
                    elif row['Distance'] > MAX_PRACTICAL_DISTANCE:
                        df.loc[idx, 'Distance'] = MAX_PRACTICAL_DISTANCE
        return df

    def process_data(self, args, shot_type):
        symbol = args.symbol
        is_ultrashort = True if args.ultrashortmode else False
        is_moonbot = True if args.moonbot else False
        is_future = True if args.future else False
        shots_data_df = self._shots_data_df[(self._shots_data_df['symbol_name'] == args.symbol) & (self._shots_data_df['shot_type'] == shot_type)]
        print("\nProcessing {} shot type...".format(shot_type))
        total_shots_count = len(shots_data_df)
        print("Length of {} shots dataframe: {}".format(symbol, total_shots_count))

        if total_shots_count == 0:
            print("No input shots data to process. Exiting.")
            return

        groups_df = shots_data_df.groupby(["shot_depth"]).size().reset_index(name='counts')
        shots_data_df = self.simulate_shots(is_ultrashort, is_moonbot, is_future, groups_df)

        if len(shots_data_df) > 0:
            if CREATE_PNL_FILE_FLAG:
                self.write_pnl_data_to_file(args, shots_data_df, shot_type)
            shots_data_df = self.get_best_pnl_rows(shots_data_df)
            shots_data_df = self.adjust_distance(is_ultrashort, is_moonbot, shots_data_df)
            self.write_best_pnl_rows_to_file(args, total_shots_count, shots_data_df, shot_type)
        else:
            print("There were no best PnL entries calculated, probably minimum distance is too high.")

    def run(self):
        args = self.parse_args()

        self._shotsdata_filename = self.get_shotsdata_filename(args)
        self._shots_data_df = self.read_csv_data(self._shotsdata_filename)
        if self._shots_data_df is None or self._shots_data_df.empty:
            print("*** No shots data found! Exiting.")
            exit(-1)

        if args.future:
            self.process_data(args, "LONG")
            self.process_data(args, "SHORT")
        else:
            self.process_data(args, "LONG")

        self.sort_best_pnl_file_rows(args)


def main():
    step = ShotsPnlCalculator()
    step.run()


if __name__ == '__main__':
    main()
