import argparse
import pandas as pd
import os
import csv
from datetime import datetime

DETECT_PRESHOT_SMA_FIELD_NAME = "SMA3"
FIND_BOUNCE_SMA_FIELD_NAME = "SMA40"

PRESHOT_TRADES_MIN_NUMBER_THRESHOLD = 3
PRESHOT_DEPTH_MIN_THRESHOLD_PCT = 0.1

SHOT_DEPTH_MIN_THRESHOLD_PCT_US_MODE = 0.2
SHOT_DEPTH_MIN_THRESHOLD_PCT = 0.4

SHOT_ROUNDING_PRECISION = 0.01

LAST_FOUND_SHOT_ALLOWANCE_MSEC = 50
SHOT_BOUNCE_LOOKUP_START = 300
SHOT_BOUNCE_LOOKUP_WINDOW = 200
SHOT_BOUNCE_LOOKUP_LIMIT = 5000
SHOT_BOUNCE_LOOKUP_WINDOW_MIN_TRADES = 3
SHOT_BOUNCE_SMA_DIFF_THRESHOLD = 0.03

MULTISHOT_MODE_FLAG = True
MULTIPLE_SHOTS_INITIAL_COUNT = 2
MULTIPLE_SHOTS_INITIAL_INTERVAL_MSEC = 1500
MULTIPLE_SHOTS_COMBINE_INTERVAL_MSEC = 7500


class Shot(object):
    def __init__(self, symbol_name, is_multishot, start_timestamp, end_timestamp, start_datetime, end_datetime, shot_trades_num, shot_type,
                       start_price, end_price, shot_duration, shot_depth, diff_with_preshot, shot_bounce, shot_bounce_ratio, shot_bounce_datetime, real_shot_depth,
                       d5m, d15m, d1H, dBTC5m, dBTC15m, dBTC1H):
        self.symbol_name = symbol_name
        self.is_multishot = is_multishot
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.shot_trades_num = shot_trades_num
        self.shot_type = shot_type
        self.start_price = start_price
        self.end_price = end_price
        self.shot_duration = shot_duration
        self.shot_depth = shot_depth
        self.diff_with_preshot = diff_with_preshot
        self.shot_bounce = shot_bounce
        self.shot_bounce_ratio = shot_bounce_ratio
        self.shot_bounce_datetime = shot_bounce_datetime
        self.real_shot_depth = real_shot_depth
        self.d5m = d5m
        self.d15m = d15m
        self.d1H = d1H
        self.dBTC5m = dBTC5m
        self.dBTC15m = dBTC15m
        self.dBTC1H = dBTC1H


class ShotBounceInfo(object):
    def __init__(self, timestamp, datetime, bounce_pct):
        self.timestamp = timestamp
        self.datetime = datetime
        self.bounce_pct = bounce_pct


class ShotsDetector(object):
    def __init__(self):
        self._trade_data_input_filename = None
        self._trade_data_df = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Shots Detector')

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

    def get_tradedata_filename(self, args):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        return '{}/../marketdata/tradedata/{}/{}/{}/{}-{}.csv'.format(dirname, args.exchange, symbol_type_str, args.symbol, args.exchange, args.symbol)

    def read_csv_data(self, filepath):
        try:
            df = pd.read_csv(filepath, index_col=[0])
        except Exception as e:
            return None
        return df

    def calculate_depth_pct(self, price1, price2):
        return abs(100 * (price2 - price1) / price1)

    def round_precision(self, val, precision):
        return round(round(val / precision) * precision, 8)

    def fmt_float(self, val):
        if val < 0.1:
            return round(val, 8)
        else:
            return val

    def get_bounce_df_pct(self, lookup_window_df, shot_type, shot_end_price):
        price_row = lookup_window_df["Price"]
        bounce_price = price_row.mean()
        if shot_type == "LONG":
            bounce_pct = 100 * (bounce_price - shot_end_price) / shot_end_price
        else:
            bounce_pct = 100 * (shot_end_price - bounce_price) / shot_end_price
        return bounce_pct

    def get_bounce_pct(self, bounce_price, shot_type, shot_end_price):
        if shot_type == "LONG":
            bounce_pct = 100 * (bounce_price - shot_end_price) / shot_end_price
        else:
            bounce_pct = 100 * (shot_end_price - bounce_price) / shot_end_price
        return bounce_pct

    def find_shot_bounce(self, df, group_timestamp, c_timestamp, c_price, shot_type, shot_end_price):
        if c_timestamp - group_timestamp > SHOT_BOUNCE_LOOKUP_START:
            c_timestamp_dt = self.to_datetime(c_timestamp)
            bounce_pct = self.get_bounce_pct(c_price, shot_type, shot_end_price)
            return ShotBounceInfo(c_timestamp, c_timestamp_dt, bounce_pct)

        lookup_cycle = 0
        total_window_start_msec = c_timestamp + SHOT_BOUNCE_LOOKUP_START
        total_window_end_msec = total_window_start_msec + SHOT_BOUNCE_LOOKUP_LIMIT
        ct = total_window_start_msec
        lookup_window_end = None
        lookup_window_end_dt = None
        lookup_window_df = None
        last_known_price = c_price
        while ct <= total_window_end_msec:
            lookup_window_start = ct
            lookup_window_start_dt = self.to_datetime(lookup_window_start)
            lookup_window_end = ct + SHOT_BOUNCE_LOOKUP_WINDOW
            lookup_window_end_dt = self.to_datetime(lookup_window_end)
            lookup_window_df = df[(df['Timestamp'] >= lookup_window_start) & (df['Timestamp'] <= lookup_window_end)]
            #print("Bounce: Lookup cycle={}, Lookup window=({},{}), Lookup dates=({},{}), duration={} msec. len(lookup_window_df)={}".format(
            #    lookup_cycle, lookup_window_start, lookup_window_end, lookup_window_start_dt, lookup_window_end_dt,
            #    lookup_window_end - lookup_window_start, len(lookup_window_df)))
            if len(lookup_window_df) >= SHOT_BOUNCE_LOOKUP_WINDOW_MIN_TRADES:
                sma_row = lookup_window_df[FIND_BOUNCE_SMA_FIELD_NAME]
                sma_min = sma_row.min()
                sma_max = sma_row.max()
                sma_diff_pct = 9999 if sma_min == 0 else round(100 * (sma_max - sma_min) / sma_min, 3)
                if sma_diff_pct <= SHOT_BOUNCE_SMA_DIFF_THRESHOLD:
                    #print("Found interval with trade data. sma_min={}, sma_max={}, sma_diff_pct={}".format(sma_min, sma_max, sma_diff_pct))
                    bounce_pct = self.get_bounce_df_pct(lookup_window_df, shot_type, shot_end_price)
                    last_row = lookup_window_df.tail(1)
                    return ShotBounceInfo(last_row["Timestamp"].values[0], last_row["Datetime"].values[0], bounce_pct)
            else:
                if(len(lookup_window_df) >= 1):
                    last_known_price = lookup_window_df.tail(1)["Price"].values[0]

            lookup_cycle = lookup_cycle + 1
            ct = lookup_window_end + 1

        # If reached here then take the whole total window length and try to find an average price
        lookup_window_df = df[(df['Timestamp'] >= total_window_start_msec) & (df['Timestamp'] <= total_window_end_msec)]
        if len(lookup_window_df) > 0:
            bounce_pct = self.get_bounce_df_pct(lookup_window_df, shot_type, shot_end_price)
            last_trade = lookup_window_df.tail(1)
            return ShotBounceInfo(last_trade["Timestamp"].values[0], last_trade["Datetime"].values[0], bounce_pct)
        else:
            bounce_pct = self.get_bounce_pct(last_known_price, shot_type, shot_end_price)
            return ShotBounceInfo(lookup_window_end, lookup_window_end_dt, bounce_pct)

    def to_datetime(self, timestamp):
        return "{}.{:03d}".format(datetime.fromtimestamp(int(timestamp / 1000)).strftime("%Y-%m-%dT%H:%M:%S"),
                                  timestamp % 1000)

    def find_shots(self, args, df, groups_df):
        symbol_name = args.symbol
        shots_list = []
        last_shot = None
        idx = 0
        for index, row in groups_df.iterrows():
            if idx % 1000 == 0:
                print("Processed {} pre-shots. Number of shots found: {}".format(idx, len(shots_list)))
            idx = idx + 1
            group_timestamp = row["Timestamp"]
            group_datetime = row["Datetime"]
            group_trade_count = row["counts"]
            shot_trades_num = group_trade_count
            trade_group_df = df[df['Timestamp'] == group_timestamp]
            first_trade = trade_group_df.head(1)
            last_trade = trade_group_df.tail(1)
            first_price = first_trade["Price"].values[0]
            last_price = last_trade["Price"].values[0]
            shot_type = "LONG" if last_price < first_price else "SHORT"
            preshot_depth_pct = self.calculate_depth_pct(first_price, last_price)
            max_price_val = last_price
            ci = last_trade.index.values[0]

            if not args.future and shot_type == "SHORT":
                continue

            if last_shot and group_timestamp < last_shot.end_timestamp + LAST_FOUND_SHOT_ALLOWANCE_MSEC:
                continue

            if preshot_depth_pct >= PRESHOT_DEPTH_MIN_THRESHOLD_PCT:
                try:
                    while ci < len(df) - 1:
                        ci = ci + 1
                        shot_trades_num = shot_trades_num + 1
                        p_trade = df.iloc[ci - 1]
                        c_trade = df.iloc[ci]
                        p_price = p_trade["Price"]
                        p_sma   = p_trade[DETECT_PRESHOT_SMA_FIELD_NAME]
                        c_timestamp = c_trade["Timestamp"]
                        c_datetime  = c_trade["Datetime"]
                        c_price     = c_trade["Price"]
                        c_sma       = c_trade[DETECT_PRESHOT_SMA_FIELD_NAME]
                        if shot_type == "LONG" and c_price < max_price_val or shot_type == "SHORT" and c_price > max_price_val:
                            max_price_val = c_price
                        if shot_type == "LONG" and p_price < p_sma and c_price > c_sma or shot_type == "SHORT" and p_price > p_sma and c_price < c_sma:
                            shot_depth_pct = self.calculate_depth_pct(first_price, max_price_val)
                            shot_depth_min_threshold = SHOT_DEPTH_MIN_THRESHOLD_PCT_US_MODE if args.ultrashortmode else SHOT_DEPTH_MIN_THRESHOLD_PCT
                            if shot_depth_pct >= shot_depth_min_threshold:
                                shot_bounce_info = self.find_shot_bounce(df, group_timestamp, c_timestamp, c_price, shot_type, max_price_val)
                                real_shot_depth = (shot_depth_pct + abs(shot_bounce_info.bounce_pct)) if shot_bounce_info.bounce_pct < 0 else shot_depth_pct
                                shot = Shot(symbol_name,
                                            False,
                                            group_timestamp,
                                            c_timestamp,
                                            group_datetime,
                                            c_datetime,
                                            shot_trades_num - 1,
                                            shot_type,
                                            self.fmt_float(first_price),
                                            self.fmt_float(max_price_val),
                                            c_timestamp - group_timestamp + 1,
                                            self.round_precision(shot_depth_pct, SHOT_ROUNDING_PRECISION),
                                            self.round_precision(shot_depth_pct - preshot_depth_pct, SHOT_ROUNDING_PRECISION),
                                            self.round_precision(shot_bounce_info.bounce_pct, SHOT_ROUNDING_PRECISION),
                                            int(round(shot_bounce_info.bounce_pct * 100 / shot_depth_pct, 0)),
                                            shot_bounce_info.datetime,
                                            self.round_precision(real_shot_depth, SHOT_ROUNDING_PRECISION),
                                            first_trade["d5m"].values[0],
                                            first_trade["d15m"].values[0],
                                            first_trade["d1H"].values[0],
                                            first_trade["dBTC5m"].values[0],
                                            first_trade["dBTC15m"].values[0],
                                            first_trade["dBTC1H"].values[0]
                                            )
                                last_shot = shot
                                shots_list.append(shot)
                                break
                            else:
                                break
                except Exception as e:
                    print(e)
                    print("**** Exception during collecting shots data for {} symbol! Exiting.".format(symbol_name))
                    exit(-1)

        return shots_list

    def find_shots_min_price(self, shots_list):
        price_list = [shot.start_price for shot in shots_list]
        end_price_list = [shot.end_price for shot in shots_list]
        price_list.extend(end_price_list)
        return min(price_list)

    def find_shots_max_price(self, shots_list):
        price_list = [shot.start_price for shot in shots_list]
        end_price_list = [shot.end_price for shot in shots_list]
        price_list.extend(end_price_list)
        return max(price_list)

    def combine_multiple_shots(self, shots_list):
        shots_list_result = []
        if not MULTISHOT_MODE_FLAG:
            return shots_list

        print("Combining several shots into multishots...")

        ci = 0
        while ci < len(shots_list) - MULTIPLE_SHOTS_INITIAL_COUNT + 1:
            c_shot = shots_list[ci]
            c_shot_timestamp = c_shot.start_timestamp
            fw_shot = shots_list[ci + MULTIPLE_SHOTS_INITIAL_COUNT - 1]
            fw_shot_timestamp = fw_shot.start_timestamp
            if fw_shot_timestamp - c_shot_timestamp <= MULTIPLE_SHOTS_INITIAL_INTERVAL_MSEC:
                cj = ci + MULTIPLE_SHOTS_INITIAL_COUNT - 1
                is_last = cj == len(shots_list) - 1
                while is_last or cj < len(shots_list) - 1:
                    cj_shot = shots_list[cj]
                    cjn_shot = shots_list[cj + 1] if not is_last else shots_list[cj]
                    cjn_shot_timestamp = cjn_shot.start_timestamp
                    if is_last or cjn_shot_timestamp - c_shot_timestamp > MULTIPLE_SHOTS_COMBINE_INTERVAL_MSEC:
                        min_shot_price = self.find_shots_min_price(shots_list[ci:cj+1])
                        max_shot_price = self.find_shots_max_price(shots_list[ci:cj+1])
                        max_price_val = max_shot_price if c_shot.shot_type == "SHORT" else min_shot_price
                        shot_depth_pct = self.round_precision(self.calculate_depth_pct(c_shot.start_price, max_price_val), SHOT_ROUNDING_PRECISION)
                        multi_shot_type = "LONG" if cj_shot.end_price < c_shot.start_price else "SHORT"
                        # merge c_shot and cj_shot objects to create a new multishot
                        new_multishot = Shot(symbol_name=c_shot.symbol_name,
                                             is_multishot=True,
                                             start_timestamp=c_shot.start_timestamp,
                                             end_timestamp=cj_shot.end_timestamp,
                                             start_datetime=c_shot.start_datetime,
                                             end_datetime=cj_shot.end_datetime,
                                             shot_trades_num=0,
                                             shot_type=multi_shot_type,
                                             start_price=c_shot.start_price,
                                             end_price=cj_shot.end_price,
                                             shot_duration=cj_shot.start_timestamp - c_shot.start_timestamp + 1,
                                             shot_depth=shot_depth_pct,
                                             diff_with_preshot=0,
                                             shot_bounce=0,
                                             shot_bounce_ratio=0,
                                             shot_bounce_datetime=0,
                                             real_shot_depth=shot_depth_pct,
                                             d5m=c_shot.d5m,
                                             d15m=c_shot.d15m,
                                             d1H=c_shot.d1H,
                                             dBTC5m=c_shot.dBTC5m,
                                             dBTC15m=c_shot.dBTC15m,
                                             dBTC1H=c_shot.dBTC1H
                                            )
                        shots_list_result.append(new_multishot)
                        ci = cj + 1
                        break
                    else:
                        cj = cj + 1
                        is_last = cj == len(shots_list) - 1
            else:
                shots_list_result.append(c_shot)
                ci = ci + 1
        return shots_list_result

    def write_to_file(self, args, shots_list):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        os.makedirs(output_path, exist_ok=True)

        header = ['symbol_name', 'is_multishot', 'start_timestamp', 'end_timestamp', 'start_datetime', 'end_datetime', 'shot_trades_num',
                  'shot_type', 'start_price', 'end_price', 'shot_duration', 'shot_depth', 'diff_with_preshot',
                  'shot_bounce', 'shot_bounce_ratio', 'shot_bounce_datetime', 'real_shot_depth', 'd5m', 'd15m', 'd1H', 'dBTC5m', 'dBTC15m', 'dBTC1H']
        csv_rows = []
        for shot in shots_list:
            csv_rows.append([
                                shot.symbol_name,
                                shot.is_multishot,
                                shot.start_timestamp,
                                shot.end_timestamp,
                                shot.start_datetime,
                                shot.end_datetime,
                                shot.shot_trades_num,
                                shot.shot_type,
                                shot.start_price,
                                shot.end_price,
                                shot.shot_duration,
                                shot.shot_depth,
                                shot.diff_with_preshot,
                                shot.shot_bounce,
                                shot.shot_bounce_ratio,
                                shot.shot_bounce_datetime,
                                shot.real_shot_depth,
                                shot.d5m,
                                shot.d15m,
                                shot.d1H,
                                shot.dBTC5m,
                                shot.dBTC15m,
                                shot.dBTC1H
                             ])

        # Save it
        filename = '{}/shots-{}-{}.csv'.format(output_path, args.exchange, symbol_type_str)

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

    def run(self):
        global SHOT_BOUNCE_LOOKUP_START

        args = self.parse_args()
        print("\nProcessing {}: ... ".format(args.symbol))

        if args.moonbot:
            SHOT_BOUNCE_LOOKUP_START = 1000
        else:
            SHOT_BOUNCE_LOOKUP_START = 300

        self._trade_data_input_filename = self.get_tradedata_filename(args)

        self._trade_data_df = self.read_csv_data(self._trade_data_input_filename)
        if self._trade_data_df is None or self._trade_data_df.empty:
            print("*** No trade data found! Exiting.")
            exit(-1)
        groups_df = self._trade_data_df.groupby(["Timestamp", "Datetime"]).size().reset_index(name='counts')
        groups_df = groups_df[groups_df['counts'] > PRESHOT_TRADES_MIN_NUMBER_THRESHOLD]
        print("Number of pre-shots: {}\nFiltering pre-shots...".format(len(groups_df)))

        shots_list = self.find_shots(args, self._trade_data_df, groups_df)

        shots_list = self.combine_multiple_shots(shots_list)

        print("Total number of shots: {}".format(len(shots_list)))

        self.write_to_file(args, shots_list)


def main():
    step = ShotsDetector()
    step.run()


if __name__ == '__main__':
    main()
