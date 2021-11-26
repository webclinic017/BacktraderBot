import argparse
import pandas as pd
import numpy as np
import os
import itertools
import collections
import csv

string_types = str

STARTCASH = 100

MIN_TOTAL_SHOTS_COUNT = 3
SS_FILTER_MIN_SHOTS_COUNT = 0

SPOT_MAKER_FEE_PCT = 0.075
SPOT_TAKER_FEE_PCT = 0.075
SPOT_FEES_PCT = SPOT_MAKER_FEE_PCT + SPOT_TAKER_FEE_PCT
FUTURE_MAKER_FEE_PCT = 0.02
FUTURE_TAKER_FEE_PCT = 0.04
FUTURE_FEES_PCT = FUTURE_MAKER_FEE_PCT + FUTURE_TAKER_FEE_PCT
SLIPPAGE_PCT = 0.01

IS_ADJUST_DISTANCE_IN_ULTRASHORT_MODE = False
MIN_PRACTICAL_DISTANCE = 0.5
MAX_PRACTICAL_DISTANCE = 3.0

MIN_DISTANCE_PCT = 0.3
MAX_BUFFER_PCT = 0.4

MIN_TP_PCT = 0.12
MAX_TP_PCT = 0.19

MIN_SL_PCT = 0.30
MAX_SL_PCT = 0.47

MIN_RR_RATIO = 2
MAX_TP_TO_SHOT_RATIO = 0.5

MIN_TP_COUNT_GROUPS_THRESHOLD = 1

DEFAULT_MIN_STEP = 0.03
TRIAL_STEP_PCT = 0.03

DEFAULT_BOUNCE_TO_SHOT_RATIO = 1/3
CREATE_PNL_FILE_FLAG = True

RATING_VALUE_DENOMINATOR = 100
DEFAULT_BIN_ROUND_BASE = 5


class ShotTrialAnalyzer(object):
    def __init__(self):
        self.shot_trials_count = 0
        self.shot_missed_count = 0
        self.shot_triggered_sl_count = 0
        self.shot_triggered_tp_count = 0
        self.random_triggered_sl_count = 0
        self.random_triggered_tp_count = 0
        self.shot_trials_pnl_arr = []


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
            header = ['symbol_name', 'shot_type', 'total_shots_count', 'max_real_shot_depth', 'MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'Profit Rating']
        else:
            header = ['symbol_name', 'shot_type', 'total_shots_count', 'max_real_shot_depth', 'Distance', 'Buffer', 'TP', 'SL', 'Profit Rating']

        csv_rows = []
        for index, row in df.iterrows():
            csv_rows.append([
                                args.symbol,
                                shot_type,
                                total_shots_count,
                                row['max_real_shot_depth'],
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

    def get_simulation_params(self, is_moonbot, shot_depth_list, shot_count_list):
        non_zero_idx = [i for i, item in enumerate(shot_count_list) if item != 0][-1]
        max_s = shot_depth_list[non_zero_idx]
        max_tp = max(MAX_TP_PCT, max_s * DEFAULT_BOUNCE_TO_SHOT_RATIO)

        if is_moonbot:
            price_min_val = np.arange(MIN_DISTANCE_PCT, max_s - 0.1 + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP)
            price_val = np.arange(MIN_DISTANCE_PCT, max_s + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP)
            tp_val = np.arange(MIN_TP_PCT, max_tp, DEFAULT_MIN_STEP)
            return {
                "MShotPriceMin": price_min_val,
                "MShotPrice": price_val,
                "tp": tp_val,
                "sl": np.arange(MIN_SL_PCT, MAX_SL_PCT, DEFAULT_MIN_STEP)
            }
        else:
            dist_val = np.arange(MIN_DISTANCE_PCT, max_s + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP)
            buffer_val = np.arange(0.2, MAX_BUFFER_PCT, DEFAULT_MIN_STEP)
            tp_val = np.arange(MIN_TP_PCT, max_tp, DEFAULT_MIN_STEP)
            sl_val = np.arange(MIN_SL_PCT, MAX_SL_PCT, DEFAULT_MIN_STEP)
            return {
                "distance": dist_val,
                "buffer": buffer_val,
                "tp": tp_val,
                "sl": sl_val
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

    def get_sim_combinations(self, is_moonbot, shot_depth_list, shot_count_list):
        simulation_params = self.get_simulation_params(is_moonbot, shot_depth_list, shot_count_list)
        kwargz = simulation_params
        optkeys = list(simulation_params)
        vals = self.iterize(kwargz.values())
        optvals = itertools.product(*vals)
        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)
        optkwargs = map(dict, okwargs1)
        return list(optkwargs)

    def calculate_shot_trials(self, is_moonbot, is_future, trial_analyzer, shot, param_arr):
        trial_analyzer.shot_trials_pnl_arr = []
        shot_depth = shot['shot_depth']
        shot_bounce = shot_depth * DEFAULT_BOUNCE_TO_SHOT_RATIO
        first_param = param_arr[0]
        second_param = param_arr[1]
        c_tp = param_arr[2]
        c_sl = param_arr[3]
        fees_pct = FUTURE_FEES_PCT if is_future else SPOT_FEES_PCT

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
                trial_pnl_pct = -(c_sl + fees_pct + SLIPPAGE_PCT)
                trial_analyzer.shot_triggered_sl_count += 1
            else:
                if shot_bounce_end >= c_tp:
                    # Shot has triggered TP
                    trial_pnl_pct = c_tp - fees_pct
                    trial_analyzer.shot_triggered_tp_count += 1
                else:
                    dist_to_tp_pct = abs(c_tp - shot_bounce_end)
                    dist_to_sl_pct = abs(-c_sl - shot_bounce_end)
                    if dist_to_tp_pct <= dist_to_sl_pct:
                        # Random price movement - count as TP
                        trial_pnl_pct = c_tp - fees_pct
                        trial_analyzer.random_triggered_tp_count += 1
                    else:
                        # Random price movement - count as SL
                        trial_pnl_pct = -(c_sl + fees_pct + SLIPPAGE_PCT)
                        trial_analyzer.random_triggered_sl_count += 1

            trial_analyzer.shot_trials_pnl_arr.append(trial_pnl_pct)
        return trial_analyzer

    def round_base(self, x, base, prec):
        return round(base * round(float(x)/base), prec)

    def pct_val(self, val, total, base):
        return self.round_base(100 * val / total, base, 0)

    def simulate_shots(self, is_moonbot, is_future, groups_df, shots_data_dict):
        arr_out = []

        shot_depth_list = list(groups_df["real_shot_depth"].values)
        shot_count_list = list(groups_df["counts"].values)
        max_real_shot_depth = max(shot_depth_list)

        combinations = self.get_sim_combinations(is_moonbot, shot_depth_list, shot_count_list)
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
                comb_params_arr = [c_mshot_price_min, c_mshot_price, c_tp, c_sl]
            else:
                c_distance = c_dict["distance"]
                c_buffer = c_dict["buffer"]
                if c_distance <= c_buffer / 2:
                    continue
                if c_tp > ((c_distance + c_buffer / 2) / MAX_TP_TO_SHOT_RATIO):
                    continue
                comb_params_arr = [c_distance, c_buffer, c_tp, c_sl]

            trial_analyzer = ShotTrialAnalyzer()
            shot_pnl_arr = []

            for index, shot_group in groups_df.iterrows():
                shot_depth = shot_group["real_shot_depth"]
                if shot_group["counts"] == 0:
                    continue

                group_shots_list = shots_data_dict[shot_depth]
                for shot in group_shots_list:
                    trial_analyzer = self.calculate_shot_trials(is_moonbot, is_future, trial_analyzer, shot, comb_params_arr)

                    if trial_analyzer:
                        if len(trial_analyzer.shot_trials_pnl_arr) > 0:
                            shot_trials_pnl_avg = np.mean(trial_analyzer.shot_trials_pnl_arr)
                            shot_pnl_arr.append(shot_trials_pnl_avg)
                        else:
                            shot_pnl_arr.append(0)

            if len(shot_pnl_arr) > 0:
                total_pnl = sum(shot_pnl_arr)
                distance_r = (comb_params_arr[1] + comb_params_arr[1] - comb_params_arr[0]) if is_moonbot else (comb_params_arr[0] + comb_params_arr[1])
                distance_rating = self.round_base(round(distance_r * RATING_VALUE_DENOMINATOR), DEFAULT_BIN_ROUND_BASE, 0)
                profit_rating = self.round_base(round(total_pnl * RATING_VALUE_DENOMINATOR), DEFAULT_BIN_ROUND_BASE, 0)
                trials_count = trial_analyzer.shot_trials_count

                arr = [round(comb_params_arr[0], 2),
                       round(comb_params_arr[1], 2),
                       round(c_tp, 2),
                       round(c_sl, 2),
                       max_real_shot_depth,
                       distance_rating,
                       profit_rating,
                       trials_count
                ]
                arr_out.append(arr)

        if is_moonbot:
            df = pd.DataFrame(arr_out, columns=['MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'max_real_shot_depth', 'Distance Rating', 'Profit Rating', 'shot_trials_count'])
        else:
            df = pd.DataFrame(arr_out, columns=['Distance', 'Buffer', 'TP', 'SL', 'max_real_shot_depth', 'Distance Rating', 'Profit Rating', 'shot_trials_count'])

        df = df.sort_values(by=['Profit Rating'], ascending=False)
        return df

    def get_best_pnl_rows(self, df):
        df = df.sort_values(by=['Profit Rating'], ascending=False)
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

        if total_shots_count <= MIN_TOTAL_SHOTS_COUNT:
            print("Number of shots is too low: {}. Exiting.".format(total_shots_count))
            return

        groups_df = shots_data_df.groupby(["real_shot_depth"]).size().reset_index(name='counts')

        shots_data_dict = {}
        for idx, row in groups_df.iterrows():
            shot_depth = row['real_shot_depth']
            group_shots_df = shots_data_df[shots_data_df['real_shot_depth'] == shot_depth]
            group_shots_list = []
            for ii, group_row in group_shots_df.iterrows():
                group_shots_list.append({'start_timestamp': group_row['start_timestamp'],
                                         'shot_depth': group_row['real_shot_depth'],
                                         'shot_bounce': group_row['shot_bounce']})
            shots_data_dict[shot_depth] = group_shots_list
        shots_data_df = self.simulate_shots(is_moonbot, is_future, groups_df, shots_data_dict)

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
