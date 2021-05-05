import ccxt
from datetime import datetime
import argparse
import pandas as pd
import time
import pytz
import csv
import os
from ccxt.base.errors import NetworkError, ExchangeError
from functools import wraps


def parse_args():
    parser = argparse.ArgumentParser(description='Binance Trade Data Downloader')

    parser.add_argument('-s','--symbol',
                        type=str,
                        required=True,
                        help='The Symbol of the Instrument/Currency Pair To Download')

    parser.add_argument('-t', '--start',
                        type=str,
                        required=True,
                        help='Start datetime')

    parser.add_argument('-e', '--end',
                        type=str,
                        required=True,
                        help='End datetime')

    parser.add_argument('-f', '--future',
                        action='store_true',
                        help=('Is instrument of future type?'))

    parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Sizer Debugs'))

    return parser.parse_args()

# Get our arguments
args = parse_args()

EXCHANGE_STR = "binance"
API_LIMIT = 1000

SMA_1_LEN = 3
SMA_2_LEN = 20
SMA_3_LEN = 40

DELTAS_ROUNDING_PRECISION = 0.01

DEFAULT_NUM_RETRIES=20
DEFAULT_BINANCE_API_DELAY=5

deltas_cache = {60: 0, 15: 0, 5: 0}
btc_deltas_cache = {60: 0, 15: 0, 5: 0}


def resolve_instrument(symbol):
    quote_curr = None
    if symbol.endswith("USDT"):
        quote_curr = "USDT"
    elif symbol.endswith("BTC"):
        quote_curr = "BTC"
    elif symbol.endswith("BUSD"):
        quote_curr = "BUSD"
    elif symbol.endswith("TUSD"):
        quote_curr = "TUSD"

    if quote_curr:
        l = len(quote_curr)
        return '{0}/{1}'.format(symbol[:-l], symbol[-l:])
    else:
        return symbol

def get_symbol_type_str(args_in):
    if args_in.future:
        return "future"
    else:
        return "spot"

# Get our Exchange
try:
    w_exchange = ccxt.binance({
        'enableRateLimit': True,

        'options': {
            'defaultType': get_symbol_type_str(args),
        }
    })
    s_exchange = ccxt.binance({
        'enableRateLimit': True,

        'options': {
            'defaultType': 'spot',
        }
    })
except AttributeError:
    print('-'*36,' ERROR ','-'*35)
    print('Exchange "{}" not found. Please check the exchange is supported.'.format(EXCHANGE_STR))
    print('-'*80)
    quit()

# Check if the symbol is available on the Exchange
w_exchange.load_markets()

instrument = resolve_instrument(args.symbol)

if instrument not in w_exchange.symbols:
    print('-'*36,' ERROR ','-'*35)
    print('The requested symbol ({}) is not available from {}\n'.format(instrument, EXCHANGE_STR))
    print('Available symbols are:')
    for key in w_exchange.symbols:
        print('  - ' + key)
    print('-'*80)
    quit()


def whereAmI():
    return os.path.dirname(os.path.realpath(__import__("__main__").__file__))


def retry(method):
    @wraps(method)
    def retry_method(*args, **kwargs):
        for i in range(DEFAULT_NUM_RETRIES):
            try:
                return method(*args, **kwargs)
            except (NetworkError, ExchangeError) as err:
                print("retry_method(): catched {}".format(type(err)))
                if i == DEFAULT_NUM_RETRIES - 1:
                    raise
                time.sleep(DEFAULT_BINANCE_API_DELAY)

    return retry_method


@retry
def fetch_ohlcv(symbol, timeframe, timestamp, api_limit):
    return s_exchange.fetch_ohlcv(symbol, timeframe, timestamp, api_limit)


def get_btc_ohlcv_data(start_timestamp, end_timestamp):
    dirname = whereAmI()
    btc_data_basepath = '{}/../marketdata/{}/{}/{}'.format(dirname, EXCHANGE_STR, "BTCUSDT", "1m")
    btc_data_filename = '{}/OHLCV-{}-{}-{}.csv'.format(btc_data_basepath, EXCHANGE_STR, "BTCUSDT", "1m")
    os.makedirs(btc_data_basepath, exist_ok=True)

    try:
        df = pd.read_csv(btc_data_filename).set_index('Timestamp')
        first_row_timestamp = df.head(1).index.values[0]
        last_row_timestamp  = df.tail(1).index.values[0]
        if start_timestamp >= first_row_timestamp and end_timestamp <= last_row_timestamp:
            print("There is an existing Spot BTC/USDT OHLC data in the file. Data will be reused.")
            return df
        else:
            print("!!! There is no Spot BTC/USDT OHLC data in the file. Data will be downloaded.")

    except:
        print("!!! Error during opening Spot BTC/USDT OHLC data file. Data will be downloaded.")

    # Get data
    timestamp = start_timestamp
    last_timestamp = None
    data = []

    while timestamp <= end_timestamp and timestamp != last_timestamp:
        print("Requesting BTCUSDT on " + datetime.fromtimestamp(int(timestamp / 1000)).strftime("%Y-%m-%dT%H:%M:%S"))
        trades = fetch_ohlcv("BTC/USDT", "1m", timestamp, API_LIMIT)
        last_timestamp = timestamp
        timestamp = trades[-1][0]
        data.extend(trades)
        if len(data) > 0 and len(trades) > 1:
            del data[-1]

    for t in data:
        dt = datetime.fromtimestamp(int(t[0] / 1000)).strftime("%Y-%m-%dT%H:%M:%S")
        t.insert(1, dt)

    header = ['Timestamp', 'Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.DataFrame(data, columns=header).set_index('Timestamp')
    # Save it
    df.to_csv(btc_data_filename)
    print("Saved BTCUSDT 1m OHLC candles into {}\n".format(btc_data_filename))
    return df


def sma(arr, index, len):
    if index < len:
        return 0
    s = 0
    for ii in range(len):
        s = s + arr[index - ii]["price"]
    return s / len


def calculate_delta_pct(arr, index, timestamp_start, timestamp_end):
    end_price = arr[index]["price"]
    min_v = end_price
    max_v = end_price
    ct = timestamp_end
    ci = index

    c_price = end_price
    while ct >= timestamp_start:
        ci = ci - 1
        ct = arr[ci]["timestamp"]
        c_price = arr[ci]["price"]
        if c_price > max_v:
            max_v = c_price
        if c_price < min_v:
            min_v = c_price

    delta_sign = 1 if c_price <= end_price else -1

    return delta_sign * 100 * (max_v - min_v) / min_v


def calculate_btc_delta_pct(btc_df, btc_timestamp_start, btc_timestamp_end):
    btc_delta_rows_df = btc_df.loc[(btc_df.index >= btc_timestamp_start) & (btc_df.index < btc_timestamp_end)]

    if len(btc_delta_rows_df) == 0:
        return 0

    first_row = btc_delta_rows_df.head(1)
    first_low = first_row["Low"].values[0]
    first_high = first_row["High"].values[0]
    min_v = first_low
    max_v = first_high

    c_low = first_low
    c_high = first_high
    for index, row in btc_delta_rows_df.iterrows():
        c_low = row["Low"]
        c_high = row["High"]
        if c_high > max_v:
            max_v = c_high
        if c_low < min_v:
            min_v = c_low

    delta_sign = -1 if c_low < first_low and c_high < first_high else 1

    return delta_sign * 100 * (max_v - min_v) / min_v


def get_instrument_delta(arr, index, delta_minutes):
    timestamp0 = arr[0]["timestamp"]
    timestamp_curr = arr[index]["timestamp"]
    diff_mins = (timestamp_curr - timestamp0) / (60 * 1000)
    curr_tick_mins = int(timestamp_curr / (60 * 1000))
    if diff_mins < delta_minutes:
        return 0

    timestamp_prev = arr[index-1]["timestamp"]
    prev_tick_mins = int(timestamp_prev / (60 * 1000))

    if curr_tick_mins > prev_tick_mins:
        delta_period_msec = delta_minutes * 60 * 1000
        deltas_cache[delta_minutes] = calculate_delta_pct(arr, index, timestamp_curr - delta_period_msec, timestamp_curr)

    return deltas_cache[delta_minutes]


def get_btc_delta(arr, index, btc_df, btc_delta_minutes):
    timestamp0 = arr[0]["timestamp"]
    timestamp_curr = arr[index]["timestamp"]
    diff_mins = (timestamp_curr - timestamp0) / (60 * 1000)
    curr_tick_mins = int(timestamp_curr / (60 * 1000))
    if diff_mins < btc_delta_minutes:
        return 0

    timestamp_prev = arr[index-1]["timestamp"]
    prev_tick_mins = int(timestamp_prev / (60 * 1000))

    if curr_tick_mins > prev_tick_mins:
        btc_delta_period_msec = btc_delta_minutes * 60 * 1000
        btc_timestamp_start = int((timestamp_curr - btc_delta_period_msec) / (60 * 1000)) * 60 * 1000
        btc_timestamp_end   = int(timestamp_curr / (60 * 1000)) * 60 * 1000
        btc_deltas_cache[btc_delta_minutes] = calculate_btc_delta_pct(btc_df, btc_timestamp_start, btc_timestamp_end)

    return btc_deltas_cache[btc_delta_minutes]


def round_precision(val, precision):
    return round(round(val / precision) * precision, 8)


def fmt_float(val):
    if val < 0.001:
        return "{:.8f}".format(val)
    else:
        return val

@retry
def fetch_trades(symbol, since, limit, params):
    return w_exchange.fetch_trades(symbol, since, limit, params)

symbol_out = instrument.replace("/","")
dirname = whereAmI()
symbol_type_str = get_symbol_type_str(args)
output_path = '{}/../marketdata/tradedata/{}/{}/{}'.format(dirname, EXCHANGE_STR, symbol_type_str, symbol_out)
os.makedirs(output_path, exist_ok=True)

gmt3_tz = pytz.timezone('Etc/GMT-3')
start_utc_date = datetime.strptime(args.start, '%Y-%m-%dT%H:%M:%S')
start_utc_date = gmt3_tz.localize(start_utc_date, is_dst=True)
start = int(start_utc_date.timestamp()) * 1000

end_utc_date = datetime.strptime(args.end, '%Y-%m-%dT%H:%M:%S')
end_utc_date = gmt3_tz.localize(end_utc_date, is_dst=True)
end = int(end_utc_date.timestamp()) * 1000

timestamp = start
last_timestamp = None
data = []

print("\n********** Started at {} **********\n".format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
print("Downloading {}...".format(args.symbol))

btc_1m_ohlc_df = get_btc_ohlcv_data(start, end)

while timestamp <= end and timestamp != last_timestamp:
    print("Requesting {} {}: {} GMT+03:00".format("Future" if args.future else "Spot", symbol_out, datetime.fromtimestamp(int(timestamp/1000)).strftime("%Y-%m-%dT%H:%M:%S")))
    options = {'startTime': timestamp, 'limit': API_LIMIT}
    if not args.future:
        options = {'startTime': timestamp, 'endTime': timestamp + 3600000}
    trades = fetch_trades(instrument, None, None, options)
    last_timestamp = timestamp
    if len(trades) > 0:
        timestamp = trades[-1]['timestamp'] + 1
        data.extend(trades)
    else:
        timestamp = timestamp + 5 * 60 * 1000
        print("Could not retrieve data on previous step. Trying with next timestamp={}".format(timestamp))


print("Downloaded {} records!\n".format(len(data)))

header = ['ID', 'Timestamp', 'Trade ID', 'Datetime', 'Side', 'Price', 'Amount', 'isBuyerMaker', 'SMA{}'.format(SMA_1_LEN), 'SMA{}'.format(SMA_2_LEN), 'SMA{}'.format(SMA_3_LEN), 'd5m', 'd15m', 'd1H', 'dBTC5m', 'dBTC15m', 'dBTC1H']
csv_rows = []

for index, data_row in enumerate(data):
    sma1 = sma(data, index, SMA_1_LEN)
    sma2 = sma(data, index, SMA_2_LEN)
    sma3 = sma(data, index, SMA_3_LEN)

    d5m  = get_instrument_delta(data, index, 5)
    d15m = get_instrument_delta(data, index, 15)
    d1h  = get_instrument_delta(data, index, 60)

    dBTC5m  = get_btc_delta(data, index, btc_1m_ohlc_df, 5)
    dBTC15m = get_btc_delta(data, index, btc_1m_ohlc_df, 15)
    dBTC1h  = get_btc_delta(data, index, btc_1m_ohlc_df, 60)

    csv_rows.append([   index,
                        data_row["timestamp"],
                        data_row["id"],
                        "{}.{:03d}".format(datetime.fromtimestamp(int(data_row["timestamp"] / 1000)).strftime("%Y-%m-%dT%H:%M:%S"), data_row["timestamp"] % 1000),
                        data_row["side"],
                        fmt_float(data_row["price"]),
                        fmt_float(data_row["amount"]),
                        1 if data_row["info"]["m"] is True else 0,
                        fmt_float(round(sma1, 8)),
                        fmt_float(round(sma2, 8)),
                        fmt_float(round(sma3, 8)),
                        round_precision(d5m,  DELTAS_ROUNDING_PRECISION),
                        round_precision(d15m, DELTAS_ROUNDING_PRECISION),
                        round_precision(d1h,  DELTAS_ROUNDING_PRECISION),
                        round_precision(dBTC5m,  DELTAS_ROUNDING_PRECISION),
                        round_precision(dBTC15m, DELTAS_ROUNDING_PRECISION),
                        round_precision(dBTC1h,  DELTAS_ROUNDING_PRECISION),
                     ])

# Save it
filename = '{}/{}-{}.csv'.format(output_path, EXCHANGE_STR, symbol_out)

ofile = open(filename, "w")
writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

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