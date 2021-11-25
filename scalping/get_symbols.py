import argparse
import requests
import io
import os


class GetSymbols(object):
    def __init__(self):
        self._trade_data_input_filename = None
        self._trade_data_df = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Binance instrument downloader')

        parser.add_argument('-f', '--future',
                            action='store_true',
                            help=('Is instrument of future type?'))

        parser.add_argument('-q', '--quoteasset',
                            type=str,
                            required=True,
                            help=('Quote asset'))

        return parser.parse_args()

    def run(self):
        args = self.parse_args()

        if args.future:
            url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
            filename = "symbols_future_{}.txt".format(args.quoteasset.lower())
        else:
            url = "https://api.binance.com/api/v1/exchangeInfo"
            filename = "symbols_spot_{}.txt".format(args.quoteasset.lower())
        headers = {}
        params = ()

        response = requests.get(url, headers=headers, params=params)
        json = response.json()

        lev_string_down = "DOWN{}".format(args.quoteasset)
        lev_string_up = "UP{}".format(args.quoteasset)
        symbol_list = [s["symbol"] for s in json["symbols"] if s["status"] == "TRADING" and s["quoteAsset"] == args.quoteasset and not lev_string_down in s["symbol"] and not lev_string_up in s["symbol"]]
        symbol_list.sort()

        symbol_list_str = "\n".join(symbol_list)
        print("Retrieved {} latest Binance {} instruments.".format(len(symbol_list), args.quoteasset))
        self.write_file(filename, symbol_list_str)



    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def write_file(self, filename, data):
        with io.open(filename, 'w', newline='\n') as f:
            f.write(data)

def main():
    step = GetSymbols()
    step.run()


if __name__ == '__main__':
    main()
