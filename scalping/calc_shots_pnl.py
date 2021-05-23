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

MIN_DISTANCE_PCT = 0.25
MIN_TP_PCT_SPOT = 0.26
MIN_TP_PCT_FUTURE = 0.12
DEFAULT_MIN_STEP = 0.02
TRIAL_STEP_PCT = 0.02

MAX_SL_PCT = 0.41

FUTURE_MIN_RR_RATIO = 2
SPOT_TP_TO_DISTANCE_RATIO_MIN = 0.3
SPOT_TP_TO_DISTANCE_RATIO_MAX = 0.4

MAX_TP_TO_SHOT_RATIO = 0.5
CREATE_PNL_FILE_FLAG = True

RATING_VALUE_DENOMINATOR = 100
DEFAULT_BIN_ROUND_BASE = 5

MIN_TP_COUNT_GROUPS_THRESHOLD = 1


class ShotTrialAnalyzer(object):
    def __init__(self):
        self.shot_trials_count = 0
        self.shot_missed_count = 0
        self.shot_triggered_sl_count = 0
        self.shot_triggered_tp_count = 0
        self.shot_trials_pnl_arr = []


class ShotsPnlCalculator(object):
    def __init__(self):
        self._shotsdata_filename = None
        self._shots_data_df = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Shots PnL Calculator')

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

    def write_pnl_data_to_file(self, args, df):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        os.makedirs(output_path, exist_ok=True)

        # Save it
        suffix = "mb" if args.moonbot else "mt"
        filename = '{}/shots-pnl-{}-{}-{}-{}.csv'.format(output_path, args.exchange, symbol_type_str, args.symbol, suffix)
        df.to_csv(filename)

    def write_best_pnl_rows_to_file(self, args, total_shots_count, df):
        # Save it
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        os.makedirs(output_path, exist_ok=True)

        if args.moonbot:
            header = ['symbol_name', 'total_shots_count', 'MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'Profit Rating']
        else:
            header = ['symbol_name', 'total_shots_count', 'Distance', 'Buffer', 'TP', 'SL', 'Profit Rating']

        csv_rows = []
        for index, row in df.iterrows():
            csv_rows.append([
                                args.symbol,
                                total_shots_count,
                                row['MShotPriceMin'] if args.moonbot else row['Distance'],
                                row['MShotPrice'] if args.moonbot else row['Buffer'],
                                row['TP'],
                                row['SL'],
                                row['Profit Rating']
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

    def get_simulation_params(self, is_moonbot, is_future, shot_depth_list, shot_count_list):
        non_zero_idx = [i for i, item in enumerate(shot_count_list) if item != 0][-1]
        max_s = shot_depth_list[non_zero_idx]
        min_tp_pct = MIN_TP_PCT_FUTURE if is_future else MIN_TP_PCT_SPOT
        max_distance = MIN_DISTANCE_PCT if MIN_DISTANCE_PCT > (max_s + DEFAULT_MIN_STEP) else (max_s + DEFAULT_MIN_STEP)

        if is_moonbot:
            return {
                "MShotPriceMin": np.arange(MIN_DISTANCE_PCT, max_distance - 0.1, DEFAULT_MIN_STEP),
                "MShotPrice": np.arange(MIN_DISTANCE_PCT, max_distance, DEFAULT_MIN_STEP),
                "tp": np.arange(min_tp_pct, (max_s + 0.2 / 2) * MAX_TP_TO_SHOT_RATIO + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP),
                "sl": np.arange(0.35, MAX_SL_PCT, DEFAULT_MIN_STEP)
            }
        else:
            return {
                "distance": np.arange(MIN_DISTANCE_PCT, max_distance, DEFAULT_MIN_STEP),
                "buffer": 0.2,
                "tp": np.arange(min_tp_pct, (max_s + 0.2 / 2) * MAX_TP_TO_SHOT_RATIO + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP),
                "sl": np.arange(0.35, MAX_SL_PCT, DEFAULT_MIN_STEP)
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

    def get_sim_combinations(self, is_moonbot, is_future, shot_depth_list, shot_count_list):
        simulation_params = self.get_simulation_params(is_moonbot, is_future, shot_depth_list, shot_count_list)
        kwargz = simulation_params
        optkeys = list(simulation_params)
        vals = self.iterize(kwargz.values())
        optvals = itertools.product(*vals)
        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)
        optkwargs = map(dict, okwargs1)
        return list(optkwargs)

    def calculate_shot_trials(self, is_moonbot, trial_analyzer, shot, param_arr):
        trial_analyzer.shot_trials_pnl_arr = []
        shot_depth = shot['shot_depth']
        shot_bounce = shot['shot_bounce']
        first_param = param_arr[0]
        second_param = param_arr[1]
        c_tp = param_arr[2]
        c_sl = param_arr[3]

        if is_moonbot:
            trials_range = np.arange(0, (second_param - first_param) + 0.01, TRIAL_STEP_PCT)
        else:
            trials_range = np.arange(0, second_param + TRIAL_STEP_PCT, TRIAL_STEP_PCT)

        for trd in trials_range:
            trial_analyzer.shot_trials_count += 1
            if is_moonbot:
                shot_trial_start = second_param - trd
            else:
                shot_trial_start = first_param + second_param / 2 - trd
            shot_trial_end = shot_trial_start - shot_depth
            if shot_trial_end > 0:  # Shot too short - limit order was not triggered. Skip this trial.
                trial_analyzer.shot_missed_count += 1
                continue
            shot_bounce_end = shot_trial_end + shot_bounce
            if shot_trial_end < -c_sl or shot_bounce_end < -c_sl:
                # Shot has triggered SL
                trial_pnl_pct = -(c_sl + COMMISSIONS_PCT + SLIPPAGE_PCT)
                trial_analyzer.shot_triggered_sl_count += 1
            else:
                if shot_bounce_end >= c_tp:
                    # Shot has triggered TP
                    trial_pnl_pct = c_tp - COMMISSIONS_PCT
                    trial_analyzer.shot_triggered_tp_count += 1
                else:
                    dist_to_tp_pct = abs(c_tp - shot_bounce_end)
                    dist_to_sl_pct = abs(-c_sl - shot_bounce_end)
                    if dist_to_tp_pct <= dist_to_sl_pct:
                        # Count as TP
                        trial_pnl_pct = c_tp - COMMISSIONS_PCT
                        trial_analyzer.shot_triggered_tp_count += 1
                    else:
                        # Count as SL
                        trial_pnl_pct = -(c_sl + COMMISSIONS_PCT + SLIPPAGE_PCT)
                        trial_analyzer.shot_triggered_sl_count += 1

            trial_analyzer.shot_trials_pnl_arr.append(trial_pnl_pct)
        return trial_analyzer

    def round_base(self, x, base, prec):
        return round(base * round(float(x)/base), prec)

    def pct_val(self, val, total, base):
        return self.round_base(100 * val / total, base, 0)

    def simulate_shots(self, is_moonbot, is_future, groups_df, shots_data_dict):
        arr_out = []

        shot_depth_list = list(groups_df["shot_depth"].values)
        shot_count_list = list(groups_df["counts"].values)

        combinations = self.get_sim_combinations(is_moonbot, is_future, shot_depth_list, shot_count_list)
        for c_idx, c_dict in enumerate(combinations):
            if c_idx % 100 == 0:
                print("{}/{}".format(c_idx, len(combinations)))
            c_tp = c_dict["tp"]
            c_sl = c_dict["sl"]
            if is_moonbot:
                c_mshot_price_min = c_dict["MShotPriceMin"]
                c_mshot_price = c_dict["MShotPrice"]
                param_arr = [c_mshot_price_min, c_mshot_price, c_tp, c_sl]
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
            else:
                c_distance = c_dict["distance"]
                c_buffer = c_dict["buffer"]
                param_arr = [c_distance, c_buffer, c_tp, c_sl]
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

            trial_analyzer = ShotTrialAnalyzer()
            shot_pnl_arr = []

            for index, shot_group in groups_df.iterrows():
                shot_depth = shot_group["shot_depth"]
                if shot_group["counts"] == 0:
                    continue

                group_shots_list = shots_data_dict[shot_depth]
                for shot in group_shots_list:
                    trial_analyzer = self.calculate_shot_trials(is_moonbot, trial_analyzer, shot, param_arr)

                    if trial_analyzer and len(trial_analyzer.shot_trials_pnl_arr) > 0:
                        shot_trials_pnl_avg = np.mean(trial_analyzer.shot_trials_pnl_arr)
                        shot_pnl_arr.append(shot_trials_pnl_avg)

            if len(shot_pnl_arr) > 0:
                total_pnl = sum(shot_pnl_arr)
                distance = (param_arr[1] + param_arr[1] - param_arr[0]) if is_moonbot else (param_arr[0] + param_arr[1])
                distance_rating = self.round_base(round(distance * RATING_VALUE_DENOMINATOR), DEFAULT_BIN_ROUND_BASE, 0)
                profit_rating = self.round_base(round(total_pnl * RATING_VALUE_DENOMINATOR), DEFAULT_BIN_ROUND_BASE, 0)
                trials_count = trial_analyzer.shot_trials_count
                arr = [round(param_arr[0], 2),
                       round(param_arr[1], 2),
                       round(c_tp, 2),
                       round(c_sl, 2),
                       distance_rating,
                       profit_rating,
                       trials_count,
                       self.pct_val(trial_analyzer.shot_missed_count, trials_count, DEFAULT_BIN_ROUND_BASE),
                       self.pct_val(trial_analyzer.shot_triggered_tp_count, trials_count, DEFAULT_BIN_ROUND_BASE),
                       self.pct_val(trial_analyzer.shot_triggered_sl_count, trials_count, DEFAULT_BIN_ROUND_BASE)]
                arr_out.append(arr)

        if is_moonbot:
            df = pd.DataFrame(arr_out, columns=['MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'Distance Rating', 'Profit Rating', 'shot_trials_count',
                                               'shot_missed_count, %', 'shot_triggered_tp_count, %', 'shot_triggered_sl_count, %'])
        else:
            df = pd.DataFrame(arr_out, columns=['Distance', 'Buffer', 'TP', 'SL', 'Distance Rating', 'Profit Rating', 'shot_trials_count',
                                               'shot_missed_count, %', 'shot_triggered_tp_count, %', 'shot_triggered_sl_count, %'])

        df = df.sort_values(by=['Profit Rating'], ascending=False)
        return df

    def get_best_pnl_rows(self, df):
        unique_tp_count_arr = df['shot_triggered_tp_count, %'].unique()
        unique_tp_count_arr_sorted = sorted(unique_tp_count_arr, key=lambda t: t)
        if len(unique_tp_count_arr_sorted) > 1:
            unique_tp_count_arr_sorted = unique_tp_count_arr_sorted[MIN_TP_COUNT_GROUPS_THRESHOLD:len(unique_tp_count_arr_sorted)]
            min_tp_count_val = unique_tp_count_arr_sorted[0]
        else:
            min_tp_count_val = unique_tp_count_arr_sorted[0]
        df = df[(df['Profit Rating'] > 0) & (df['shot_triggered_tp_count, %'] >= min_tp_count_val)]
        df = df.sort_values(by=['Distance'], ascending=False)
        return df.head(1)

    def process_data(self, args):
        symbol = args.symbol
        is_moonbot = True if args.moonbot else False
        is_future = True if args.future else False
        if args.future:
            shots_data_df = self._shots_data_df[self._shots_data_df['symbol_name'] == symbol]
        else:
            shots_data_df = self._shots_data_df[(self._shots_data_df['symbol_name'] == symbol) & (self._shots_data_df['shot_type'] == "LONG")]

        print("\nCalculating best PnL for {}...".format(symbol))
        total_shots_count = len(shots_data_df)
        print("Length of {} shots dataframe: {}".format(symbol, total_shots_count))

        if total_shots_count == 0:
            print("No input shots data to process. Exiting.")
            return

        groups_df = shots_data_df.groupby(["shot_depth"]).size().reset_index(name='counts')

        shots_data_dict = {}
        for idx, row in groups_df.iterrows():
            shot_depth = row['shot_depth']
            group_shots_df = shots_data_df[shots_data_df['shot_depth'] == shot_depth]
            group_shots_list = []
            for ii, group_row in group_shots_df.iterrows():
                group_shots_list.append({'start_timestamp': group_row['start_timestamp'],
                                         'shot_depth': group_row['shot_depth'],
                                         'shot_bounce': group_row['shot_bounce']})
            shots_data_dict[shot_depth] = group_shots_list
        shots_data_df = self.simulate_shots(is_moonbot, is_future, groups_df, shots_data_dict)

        if len(shots_data_df) > 0:
            if CREATE_PNL_FILE_FLAG:
                self.write_pnl_data_to_file(args, shots_data_df)
            shots_data_df = self.get_best_pnl_rows(shots_data_df)
            self.write_best_pnl_rows_to_file(args, total_shots_count, shots_data_df)

    def run(self):
        args = self.parse_args()

        self._shotsdata_filename = self.get_shotsdata_filename(args)
        self._shots_data_df = self.read_csv_data(self._shotsdata_filename)
        if self._shots_data_df is None or self._shots_data_df.empty:
            print("*** No shots data found! Exiting.")
            exit(-1)

        self.process_data(args)


def main():
    step = ShotsPnlCalculator()
    step.run()


if __name__ == '__main__':
    main()
