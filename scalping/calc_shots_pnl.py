import argparse
import pandas as pd
import numpy as np
import os
import itertools
import collections
import csv

string_types = str

BINS_SPLITTER = ":"

MIN_TOTAL_SHOTS_COUNT = 5

COMMISSIONS_PCT = 0.02 + 0.04
SLIPPAGE_PCT = 0.02

SS_FILTER_MIN_SHOTS_COUNT = 0

MIN_DISTANCE_PCT = 0.2
MIN_TP_PCT = 0.2
DEFAULT_MIN_STEP = 0.02
TRIAL_STEP_PCT = 0.02

DEFAULT_MT_MIN_TP_PCT = 0.1  # For MoonTrader - this is a break-even TP
DEFAULT_MB_MIN_TP_PCT = 0.2  # In MoonBot auto decresing of TP order possible

MAX_MSHOT_PRICE_MIN = 0.91
MAX_MSHOT_PRICE = 1.01
MAX_BUFFER_PCT = 0.36
MAX_SL_PCT = 0.45

MIN_RR_RATIO = 2

MAX_TP_TO_SHOT_RATIO = 0.5
CREATE_PNL_FILE_FLAG = True


class ShotTrialAnalyzer(object):
    def __init__(self):
        self.shot_trials_count = 0
        self.shot_missed_count = 0
        self.shot_triggered_sl_count = 0
        self.shot_bounce_triggered_sl_count = 0
        self.shot_triggered_tp_count = 0
        self.shot_break_even_count = 0
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
            header = ['symbol_name', 'shot_type', 'total_shots_count', 'MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'Profit Rating']
        else:
            header = ['symbol_name', 'shot_type', 'total_shots_count', 'Distance', 'Buffer', 'TP', 'SL', 'Profit Rating']

        csv_rows = []
        for index, row in df.iterrows():
            csv_rows.append([
                                args.symbol,
                                shot_type,
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

    def get_shot_depth_from_cat(self, shot_depth_cat):
        depth_info_category = shot_depth_cat.split(BINS_SPLITTER)
        min_val = float(depth_info_category[0])
        max_val = float(depth_info_category[1])
        return (min_val + max_val) / 2

    def apply_ss_filter(self, p_table_df):
        width = len(p_table_df.values[0])
        height = len(p_table_df.values)
        for i in range(height):
            for j in range(width):
                shot_count = p_table_df.values[i][j]
                p_table_df.values[i][j] = shot_count if shot_count >= SS_FILTER_MIN_SHOTS_COUNT else 0

        return p_table_df

    def get_simulation_params(self, is_moonbot, shot_depth_list, shot_count_list):
        non_zero_idx = [i for i, item in enumerate(shot_count_list) if item != 0][-1]
        max_s = shot_depth_list[non_zero_idx]

        if is_moonbot:
            return {
                "MShotPriceMin": np.arange(0.2, MAX_MSHOT_PRICE_MIN, DEFAULT_MIN_STEP),
                "MShotPrice": np.arange(0.2, MAX_MSHOT_PRICE, DEFAULT_MIN_STEP),
                "tp": np.arange(MIN_TP_PCT, MAX_MSHOT_PRICE * MAX_TP_TO_SHOT_RATIO + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP),
                "sl": np.arange(0.35, MAX_SL_PCT, DEFAULT_MIN_STEP)
            }
        else:
            return {
                "distance": np.arange(MIN_DISTANCE_PCT, max_s + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP),
                "buffer": np.arange(0.2, MAX_BUFFER_PCT, DEFAULT_MIN_STEP),
                "tp": np.arange(MIN_TP_PCT, (max_s + MAX_BUFFER_PCT / 2) * MAX_TP_TO_SHOT_RATIO + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP),
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

    def get_sim_combinations(self, is_moonbot, shot_depth_list, shot_count_list):
        simulation_params = self.get_simulation_params(is_moonbot, shot_depth_list, shot_count_list)
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
                if shot_trial_end < -c_sl:
                    trial_analyzer.shot_triggered_sl_count += 1
                elif shot_bounce_end < -c_sl:
                    trial_analyzer.shot_bounce_triggered_sl_count += 1
            else:
                if shot_bounce_end >= c_tp:
                    # Shot has triggered TP
                    trial_pnl_pct = c_tp - COMMISSIONS_PCT
                    trial_analyzer.shot_triggered_tp_count += 1
                else:
                    # Break-even TP (MoonTrader mode)
                    # In MoonBot - minimum TP through auto decreasing TP
                    assumed_tp = DEFAULT_MB_MIN_TP_PCT if is_moonbot else DEFAULT_MT_MIN_TP_PCT
                    trial_pnl_pct = assumed_tp - COMMISSIONS_PCT
                    trial_analyzer.shot_break_even_count += 1

            trial_analyzer.shot_trials_pnl_arr.append(trial_pnl_pct)
        return trial_analyzer

    def simulate_shots(self, is_moonbot, groups_df, shots_data_dict):
        arr_out = []

        shot_depth_list = list(groups_df["shot_depth"].values)
        shot_count_list = list(groups_df["counts"].values)

        combinations = self.get_sim_combinations(is_moonbot, shot_depth_list, shot_count_list)
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
                if c_sl / c_tp < MIN_RR_RATIO:
                    continue
            else:
                c_distance = c_dict["distance"]
                c_buffer = c_dict["buffer"]
                param_arr = [c_distance, c_buffer, c_tp, c_sl]
                if c_distance <= c_buffer / 2:
                    continue
                if c_tp > ((c_distance + c_buffer / 2) / MAX_TP_TO_SHOT_RATIO):
                    continue
                if c_sl / c_tp < MIN_RR_RATIO:
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
                arr = [round(param_arr[0], 2),
                       round(param_arr[1], 2),
                       round(c_tp, 2),
                       round(c_sl, 2),
                       round(total_pnl, 1),
                       trial_analyzer.shot_trials_count,
                       trial_analyzer.shot_missed_count,
                       trial_analyzer.shot_triggered_sl_count,
                       trial_analyzer.shot_bounce_triggered_sl_count,
                       trial_analyzer.shot_triggered_tp_count,
                       trial_analyzer.shot_break_even_count]
                arr_out.append(arr)

        if is_moonbot:
            df = pd.DataFrame(arr_out, columns=['MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'Profit Rating', 'shot_trials_count',
                                               'shot_missed_count', 'shot_triggered_sl_count', 'shot_bounce_triggered_sl_count',
                                               'shot_triggered_tp_count', 'shot_break_even_count'])
        else:
            df = pd.DataFrame(arr_out, columns=['Distance', 'Buffer', 'TP', 'SL', 'Profit Rating', 'shot_trials_count',
                                               'shot_missed_count', 'shot_triggered_sl_count', 'shot_bounce_triggered_sl_count',
                                               'shot_triggered_tp_count', 'shot_break_even_count'])

        df = df.sort_values(by=['Profit Rating'], ascending=False)
        return df

    def get_best_pnl_rows(self, df):
        df['add_criteria1'] = df['Profit Rating']
        df['add_criteria2'] = df['SL'] / df['TP']
        df = df.sort_values(by=['add_criteria1', 'add_criteria2'], ascending=False)
        return df.head(1)

    def process_data(self, args, shot_type):
        is_moonbot = True if args.moonbot else False
        shots_data_df = self._shots_data_df[(self._shots_data_df['symbol_name'] == args.symbol) & (self._shots_data_df['shot_type'] == shot_type)]
        print("\nProcessing {} shot type...".format(shot_type))
        total_shots_count = len(shots_data_df)
        print("Length of {} shots dataframe: {}".format(args.symbol, total_shots_count))

        if total_shots_count == 0:
            print("No input shots data to process. Exiting.")
            return

        if total_shots_count <= MIN_TOTAL_SHOTS_COUNT:
            print("Number of shots is too low: {}. Exiting.".format(total_shots_count))
            return

        groups_df = shots_data_df.groupby(["shot_depth"]).size().reset_index(name='counts')
        groups_df = groups_df[groups_df['counts'] >= SS_FILTER_MIN_SHOTS_COUNT]
        if len(groups_df) == 0:
            print("After filtering there is no shots data to process. Exiting.")
            return

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
        shots_data_df = self.simulate_shots(is_moonbot, groups_df, shots_data_dict)

        if len(shots_data_df) > 0:
            if CREATE_PNL_FILE_FLAG:
                self.write_pnl_data_to_file(args, shots_data_df, shot_type)
            shots_data_df = self.get_best_pnl_rows(shots_data_df)
            self.write_best_pnl_rows_to_file(args, total_shots_count, shots_data_df, shot_type)

    def run(self):
        args = self.parse_args()

        self._shotsdata_filename = self.get_shotsdata_filename(args)
        self._shots_data_df = self.read_csv_data(self._shotsdata_filename)
        if self._shots_data_df is None or self._shots_data_df.empty:
            print("*** No shots data found! Exiting.")
            exit(-1)

        self.process_data(args, "LONG")
        self.process_data(args, "SHORT")


def main():
    step = ShotsPnlCalculator()
    step.run()


if __name__ == '__main__':
    main()
