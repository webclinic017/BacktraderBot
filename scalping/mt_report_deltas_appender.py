import pandas as pd
import os
import glob
from datetime import timedelta
from scalping.binance_trade_data import BinanceTradeDataDownloader

SERVER_TO_LOCAL_TZ_ADJUST_TIMEDELTA = timedelta(hours=2)

TRADES_DOWNLOAD_START_DELTA = timedelta(minutes=90)
TRADES_DOWNLOAD_END_DELTA = timedelta(minutes=5)

DEFAULT_WORKING_PATH = "/Users/alex/Downloads"
ALL_TRADES_FILENAME = "all-trades.xlsx"
ALL_TRADES_DELTAS_FILENAME = "all-trades-deltas.xlsx"

TRADE_LOOKUP_WINDOW_SEC = 5

HEADER_COIN_DELTA_1 = 'd5m'
HEADER_COIN_DELTA_2 = 'd15m'
HEADER_COIN_DELTA_3 = 'd1H'
HEADER_BTC_DELTA_1 = 'dBTC5m'
HEADER_BTC_DELTA_2 = 'dBTC15m'
HEADER_BTC_DELTA_3 = 'dBTC1H'


class MTReportDeltaAppender(object):
    def __init__(self):
        self.trade_downloader = None
        self._model_dict = {}
        self._total_stats_dict = {}

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_trades_filename(self):
        file_search_wildcard = "{}/*{}".format(DEFAULT_WORKING_PATH, ALL_TRADES_FILENAME)
        paths = glob.glob(file_search_wildcard)
        if len(paths) == 0:
            raise Exception("No {} files found".format(file_search_wildcard))
        if len(paths) > 1:
            raise Exception("Multiple {} files found. Need to have only 1 file to process.".format(file_search_wildcard))
        return paths[0]

    def get_output_analysis_filename(self, trades_filename):
        fn = trades_filename.split("/")[-1]
        prefix = fn.split(ALL_TRADES_FILENAME)[0]
        return '{}/{}{}'.format(DEFAULT_WORKING_PATH, prefix, ALL_TRADES_DELTAS_FILENAME)

    def read_trades_data(self, trades_filename):
        try:
            df = pd.read_excel(trades_filename)
            return df
        except:
            print("!!! Error during opening {} file.".format(trades_filename))

    def get_datetime_local_tz(self, row):
        if isinstance(row, pd.DataFrame):
            return pd.to_datetime(row["entry_timestamp"].values[0]) + SERVER_TO_LOCAL_TZ_ADJUST_TIMEDELTA
        elif isinstance(row, pd.Series):
            return pd.to_datetime(row["entry_timestamp"]) + SERVER_TO_LOCAL_TZ_ADJUST_TIMEDELTA

    def get_download_daterange(self, trades_data_df, symbol):
        symbol_df = trades_data_df[trades_data_df['symbol'] == symbol]
        first_row_dt = self.get_datetime_local_tz(symbol_df.head(1))
        last_row_dt = self.get_datetime_local_tz(symbol_df.tail(1))
        start_datetime = first_row_dt - TRADES_DOWNLOAD_START_DELTA
        end_datetime = last_row_dt + TRADES_DOWNLOAD_END_DELTA
        start_datetime_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        end_datetime_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        return {"start": start_datetime_str, "end": end_datetime_str}

    def append_deltas(self, trades_data_df, symbol, is_future):
        trades_symbol_df = trades_data_df[trades_data_df['symbol'] == symbol]
        dirname = self.whereAmI()
        tick_data_filepath = self.trade_downloader.get_tick_data_filepath(dirname, symbol, is_future)
        tick_data_filename = self.trade_downloader.get_tick_data_filename(tick_data_filepath, symbol)
        tick_data_df = pd.read_csv(tick_data_filename).set_index('Timestamp')

        for index, row in trades_symbol_df.iterrows():
            trade_datetime = pd.to_datetime(row["entry_timestamp"])
            trade_timestamp_start_msec = int(trade_datetime.timestamp() * 1000)
            trade_timestamp_end_msec = int(trade_timestamp_start_msec + TRADE_LOOKUP_WINDOW_SEC * 1000)
            ticks_df = tick_data_df.loc[(tick_data_df.index >= trade_timestamp_start_msec) & (tick_data_df.index <= trade_timestamp_end_msec)]
            if len(ticks_df) > 0:
                tick_row = ticks_df.head(1).iloc[0]
                cond = (trades_data_df["entry_timestamp"] == row["entry_timestamp"]) & (trades_data_df["symbol"] == symbol)
                trades_data_df.loc[cond, HEADER_COIN_DELTA_1] = tick_row[HEADER_COIN_DELTA_1]
                trades_data_df.loc[cond, HEADER_COIN_DELTA_2] = tick_row[HEADER_COIN_DELTA_2]
                trades_data_df.loc[cond, HEADER_COIN_DELTA_3] = tick_row[HEADER_COIN_DELTA_3]
                trades_data_df.loc[cond, HEADER_BTC_DELTA_1] = tick_row[HEADER_BTC_DELTA_1]
                trades_data_df.loc[cond, HEADER_BTC_DELTA_2] = tick_row[HEADER_BTC_DELTA_2]
                trades_data_df.loc[cond, HEADER_BTC_DELTA_3] = tick_row[HEADER_BTC_DELTA_3]

        return trades_data_df

    def add_deltas_columns(self, df):
        df_new = df.assign(c1=0, c2=0, c3=0, b1=0, b2=0, b3=0)
        df_new.rename(columns={"c1": HEADER_COIN_DELTA_1, "c2": HEADER_COIN_DELTA_2, "c3": HEADER_COIN_DELTA_3, "b1": HEADER_BTC_DELTA_1, "b2": HEADER_BTC_DELTA_2, "b3": HEADER_BTC_DELTA_3}, inplace=True)
        return df_new

    def run(self, is_future):
        trades_filename = self.get_trades_filename()
        trades_data_df = self.read_trades_data(trades_filename)
        trades_data_df = self.add_deltas_columns(trades_data_df)
        symbols = list(trades_data_df['symbol'].unique())
        symbols.sort()

        for symbol in symbols:
            symbol_daterange = self.get_download_daterange(trades_data_df, symbol)

            self.trade_downloader = BinanceTradeDataDownloader()
            print("Start downloading tick data for {}...".format(symbol))
            self.trade_downloader.process(symbol, symbol_daterange["start"], symbol_daterange["end"], is_future)
            print("Finished downloading tick data for {}!".format(symbol))

            trades_data_df = self.append_deltas(trades_data_df, symbol, is_future)

        output_filename = self.get_output_analysis_filename(trades_filename)
        trades_data_df.to_excel(output_filename, engine='xlsxwriter')
        print("Written modified file: {}".format(output_filename))


def main():
    d = MTReportDeltaAppender()
    d.run(True)


if __name__ == '__main__':
    main()
