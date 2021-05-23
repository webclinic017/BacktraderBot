import argparse
import pandas as pd
import os
import csv
from datetime import datetime

DETECT_PRESHOT_SMA_FIELD_NAME = "SMA3"
FIND_BOUNCE_SMA_FIELD_NAME = "SMA40"

PRESHOT_TRADES_MIN_NUMBER_THRESHOLD = 3
PRESHOT_DEPTH_MIN_THRESHOLD_PCT = 0.1
SHOT_DEPTH_MIN_THRESHOLD_PCT = 0.2
SHOT_ROUNDING_PRECISION = 0.01

LAST_FOUND_SHOT_ALLOWANCE_MSEC = 50
SHOT_BOUNCE_LOOKUP_START = 300
SHOT_BOUNCE_LOOKUP_WINDOW = 200
SHOT_BOUNCE_LOOKUP_LIMIT = 5000
SHOT_BOUNCE_LOOKUP_WINDOW_MIN_TRADES = 3
SHOT_BOUNCE_SMA_DIFF_THRESHOLD = 0.03


class Shot(object):
    def __init__(self, symbol_name, start_timestamp, end_timestamp, start_datetime, end_datetime, shot_trades_num, shot_type,
                       start_price, end_price, shot_duration, shot_depth, diff_with_preshot, shot_bounce, shot_bounce_ratio, shot_bounce_datetime,
                       d5m, d15m, d1H, dBTC5m, dBTC15m, dBTC1H):
        self.symbol_name = symbol_name
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
            return "{:.8f}".format(val)
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
                            if shot_depth_pct >= SHOT_DEPTH_MIN_THRESHOLD_PCT:
                                shot_bounce_info = self.find_shot_bounce(df, group_timestamp, c_timestamp, c_price, shot_type, max_price_val)
                                shot = Shot(symbol_name,
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

    def write_to_file(self, args, shots_list):
        dirname = self.whereAmI()
        symbol_type_str = self.get_symbol_type_str(args)
        output_path = '{}/../marketdata/shots/{}/{}'.format(dirname, args.exchange, symbol_type_str)
        os.makedirs(output_path, exist_ok=True)

        header = ['symbol_name','start_timestamp','end_timestamp','start_datetime','end_datetime','shot_trades_num',
                  'shot_type','start_price','end_price','shot_duration','shot_depth','diff_with_preshot',
                  'shot_bounce','shot_bounce_ratio','shot_bounce_datetime','d5m','d15m','d1H','dBTC5m','dBTC15m','dBTC1H']
        csv_rows = []
        for shot in shots_list:
            csv_rows.append([
                                shot.symbol_name,
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

        print("Total number of shots: {}".format(len(shots_list)))

        self.write_to_file(args, shots_list)


def main():
    step = ShotsDetector()
    step.run()


if __name__ == '__main__':
    main()
