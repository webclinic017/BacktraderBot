'''
Author: www.backtest-rookies.com

MIT License

Copyright (c) 2018 backtest-rookies.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import ccxt
from datetime import datetime, timedelta, timezone
import math
import argparse
import pandas as pd
import time
from calendar import timegm
import pathlib
import os

def parse_args():
    parser = argparse.ArgumentParser(description='CCXT Market Data Downloader')


    parser.add_argument('-s','--symbol',
                        type=str,
                        required=True,
                        help='The Symbol of the Instrument/Currency Pair To Download')

    parser.add_argument('-e','--exchange',
                        type=str,
                        required=True,
                        help='The exchange to download from')

    parser.add_argument('-t','--timeframe',
                        type=str,
                        default='1d',
                        choices=['1m', '5m','15m', '30m','1h', '2h', '3h', '4h', '6h', '12h', '1d', '1M', '1y'],
                        help='The timeframe to download')


    parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Sizer Debugs'))

    return parser.parse_args()

# Get our arguments
args = parse_args()

# Get our Exchange
try:
    exchange = getattr (ccxt, args.exchange) ()
except AttributeError:
    print('-'*36,' ERROR ','-'*35)
    print('Exchange "{}" not found. Please check the exchange is supported.'.format(args.exchange))
    print('-'*80)
    quit()

# Check if fetching of OHLC Data is supported
if exchange.has["fetchOHLCV"] == False:
    print('-'*36,' ERROR ','-'*35)
    print('{} does not support fetching OHLC data. Please use another exchange'.format(args.exchange))
    print('-'*80)
    quit()

# Check requested timeframe is available. If not return a helpful error.
if args.timeframe not in exchange.timeframes:
    print('-'*36,' ERROR ','-'*35)
    print('The requested timeframe ({}) is not available from {}\n'.format(args.timeframe,args.exchange))
    print('Available timeframes are:')
    for key in exchange.timeframes.keys():
        print('  - ' + key)
    print('-'*80)
    quit()

# Check if the symbol is available on the Exchange
exchange.load_markets()
if args.symbol not in exchange.symbols:
    print('-'*36,' ERROR ','-'*35)
    print('The requested symbol ({}) is not available from {}\n'.format(args.symbol,args.exchange))
    print('Available symbols are:')
    for key in exchange.symbols:
        print('  - ' + key)
    print('-'*80)
    quit()


def whereAmI():
    return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

sym = args.symbol
symbol_out = args.symbol.replace("/","")
dirname = whereAmI()
output_path = '{}/marketdata/{}/{}/{}'.format(dirname, args.exchange, symbol_out, args.timeframe)
os.makedirs(output_path, exist_ok=True)

# Get data
#    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None, params={}):

start_utc_time = time.strptime("2000-01-01T00:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
start = timegm(start_utc_time) * 1000
end = time.time() * 1000
limit = 1000
timestamp = start
last_timestamp = None
data = []

while timestamp <= end and timestamp != last_timestamp:
    print("Requesting " + datetime.fromtimestamp(int(timestamp/1000)).strftime("%Y-%m-%dT%H:%M:%S"))
    trades = exchange.fetch_ohlcv(args.symbol, args.timeframe, timestamp, limit)
    last_timestamp = timestamp
    timestamp = trades[-1][0]
    data.extend(trades)
    time.sleep(6)
    if len(data) > 0 and len(trades) > 1:
        del data[-1] 

for t in data:
    t[0] = datetime.fromtimestamp(int(t[0] / 1000)).strftime("%Y-%m-%dT%H:%M:%S")

header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
df = pd.DataFrame(data, columns=header).set_index('Timestamp')
# Save it
filename = '{}/{}-{}-{}.csv'.format(output_path, args.exchange, symbol_out,args.timeframe)
df.to_csv(filename)