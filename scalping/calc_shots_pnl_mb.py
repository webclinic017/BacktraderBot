import argparse
import pandas as pd
import numpy as np
import os
import itertools
import collections
import csv

string_types = str

BINS_SPLITTER = ":"

COMMISSIONS_PCT = 0.02 + 0.04
SLIPPAGE_PCT = 0.02

SHOT_DEPTH_TO_TP_MAX_RATIO = 0.50

SS_FILTER_MIN_SHOTS_COUNT = 2

MIN_TP_PCT = 0.15
DEFAULT_MIN_STEP = 0.03
TRIAL_STEP_PCT = 0.03

DEFAULT_MB_MIN_TP_PCT = 0.2  # In MoonBot auto decresing of TP order possible

CREATE_PNL_FILE_FLAG = True

SIMULATION_PARAMS = {
    "MShotPriceMin": np.arange(0.15, 0.91, DEFAULT_MIN_STEP),
    "MShotPrice": np.arange(0.15, 1.01, DEFAULT_MIN_STEP),
    "tp": 0,
    "sl": np.arange(0.2, 0.46, DEFAULT_MIN_STEP)
}


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
        filename = '{}/shots-pnl-{}-{}-{}-{}-mb.csv'.format(output_path, args.exchange, symbol_type_str, args.symbol, shot_type)
        df.to_csv(filename)

    def write_best_pnl_rows_to_file(self, args, total_shots_count, df, shot_type):
        # Save it
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        os.makedirs(output_path, exist_ok=True)

        header = ['symbol_name', 'shot_type', 'total_shots_count', 'MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'Profit Rating']
        csv_rows = []
        for index, row in df.iterrows():
            csv_rows.append([
                                args.symbol,
                                shot_type,
                                total_shots_count,
                                row['MShotPriceMin'],
                                row['MShotPrice'],
                                row['TP'],
                                row['SL'],
                                row['Profit Rating']
                             ])

        filename = '{}/shots-best-pnl-{}-{}-mb.csv'.format(output_path, args.exchange, symbol_type_str)

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

    def update_simulation_params(self, shot_depth_list, shot_count_list):
        global SIMULATION_PARAMS
        non_zero_idx = [i for i, item in enumerate(shot_count_list) if item != 0][-1]
        max_s = shot_depth_list[non_zero_idx]
        SIMULATION_PARAMS["tp"] = np.arange(MIN_TP_PCT, max_s * SHOT_DEPTH_TO_TP_MAX_RATIO + DEFAULT_MIN_STEP, DEFAULT_MIN_STEP)

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

    def get_sim_combinations(self):
        kwargz = SIMULATION_PARAMS
        optkeys = list(SIMULATION_PARAMS)
        vals = self.iterize(kwargz.values())
        optvals = itertools.product(*vals)
        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)
        optkwargs = map(dict, okwargs1)
        return list(optkwargs)

    def calculate_shot_trials(self, shot, c_mshot_price_min, c_mshot_price, c_tp, c_sl):
        shot_trials_pnl_arr = []
        shot_depth = shot['shot_depth']
        shot_bounce = shot['shot_bounce']
        trials_range = np.arange(0, (c_mshot_price - c_mshot_price_min) + 0.01, TRIAL_STEP_PCT)
        for trd in trials_range:
            shot_trial_start = c_mshot_price - trd
            shot_trial_end = shot_trial_start - shot_depth
            if shot_trial_end > 0:  # Shot too short - limit order was not triggered. Skip this trial.
                continue
            shot_bounce_end = shot_trial_end + shot_bounce
            if shot_trial_end < -c_sl or shot_bounce_end < -c_sl:
                # Shot has triggered SL
                trial_pnl_pct = -(c_sl + COMMISSIONS_PCT + SLIPPAGE_PCT)
            else:
                if shot_bounce_end >= c_tp:
                    # Shot has triggered TP
                    trial_pnl_pct = c_tp - COMMISSIONS_PCT
                else:
                    # In MoonBot - minimum TP through auto decreasing TP
                    assumed_tp = DEFAULT_MB_MIN_TP_PCT
                    trial_pnl_pct = assumed_tp - COMMISSIONS_PCT

            shot_trials_pnl_arr.append(trial_pnl_pct)
        return shot_trials_pnl_arr

    def simulate_shots(self, groups_df, shots_data_dict):
        arr_out = []

        shot_depth_list = list(groups_df["shot_depth"].values)
        shot_count_list = list(groups_df["counts"].values)
        self.update_simulation_params(shot_depth_list, shot_count_list)

        combinations = self.get_sim_combinations()
        for c_idx, c_dict in enumerate(combinations):
            if c_idx % 100 == 0:
                print("{}/{}".format(c_idx, len(combinations)))
            c_mshot_price_min = c_dict["MShotPriceMin"]
            c_mshot_price = c_dict["MShotPrice"]
            c_tp = c_dict["tp"]
            c_sl = c_dict["sl"]
            if c_mshot_price <= c_mshot_price_min:
                continue

            shot_pnl_arr = []

            for index, shot_group in groups_df.iterrows():
                shot_depth = shot_group["shot_depth"]
                if shot_group["counts"] == 0:
                    continue

                group_shots_list = shots_data_dict[shot_depth]
                for shot in group_shots_list:
                    shot_trials_pnl_arr = self.calculate_shot_trials(shot, c_mshot_price_min, c_mshot_price, c_tp, c_sl)

                    if len(shot_trials_pnl_arr) > 0:
                        shot_trials_pnl_avg = np.mean(shot_trials_pnl_arr)
                        shot_pnl_arr.append(shot_trials_pnl_avg)

            if len(shot_pnl_arr) > 0:
                total_pnl = sum(shot_pnl_arr)
                arr = [round(c_mshot_price_min, 2), round(c_mshot_price, 2), round(c_tp, 2), round(c_sl, 2), round(total_pnl, 2)]
                arr_out.append(arr)

        df = pd.DataFrame(arr_out, columns=['MShotPriceMin', 'MShotPrice', 'TP', 'SL', 'Profit Rating'])
        df = df.sort_values(by=['Profit Rating'], ascending=False)
        return df

    def get_best_pnl_rows(self, df):
        best_pnl_rating = df.head(1)['Profit Rating'].values[0]
        df['criterion1'] = df['MShotPrice'] - df['MShotPriceMin']
        df['criterion2'] = df['TP'] / df['SL']
        df = df[df['Profit Rating'] == best_pnl_rating]
        df = df.sort_values(by=['criterion1', 'criterion2'], ascending=True)
        return df.head(1)

    def process_data(self, args, shot_type):
        shots_data_df = self._shots_data_df[(self._shots_data_df['symbol_name'] == args.symbol) & (self._shots_data_df['shot_type'] == shot_type)]
        print("\nProcessing {} shot type...".format(shot_type))
        total_shots_count = len(shots_data_df)
        print("Length of {} shots dataframe: {}".format(args.symbol, total_shots_count))

        if total_shots_count == 0:
            print("No input shots data to process. Exiting.")
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
        shots_data_df = self.simulate_shots(groups_df, shots_data_dict)

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
