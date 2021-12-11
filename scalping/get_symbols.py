import argparse
import requests
import io
import os

FUTURE_SYMBOL_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
SPOT_SYMBOL_INFO_URL = "https://api.binance.com/api/v1/exchangeInfo"

FUTURE_VOLUME_INFO_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr"
SPOT_VOLUME_INFO_URL = "https://api.binance.com/api/v1/ticker/24hr"

FUTURE_VOLUME_FILTER_USDT_VAL = 40000000
SPOT_VOLUME_FILTER_USDT_VAL = 10000000


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

    def get_volume_info(self, args):
        if args.future:
            volume_info_api_url = FUTURE_VOLUME_INFO_URL
        else:
            volume_info_api_url = SPOT_VOLUME_INFO_URL

        headers = {}
        params = ()

        response = requests.get(volume_info_api_url, headers=headers, params=params)
        json = response.json()

        volume_info_dict = {s_info_dict["symbol"]:float(s_info_dict["quoteVolume"]) for s_info_dict in json}
        return volume_info_dict

    def run(self):
        args = self.parse_args()

        if args.future:
            symbol_info_api_url = FUTURE_SYMBOL_INFO_URL
            filename = "symbols_future_{}.txt".format(args.quoteasset.lower())
            filter_val = FUTURE_VOLUME_FILTER_USDT_VAL
        else:
            symbol_info_api_url = SPOT_SYMBOL_INFO_URL
            filename = "symbols_spot_{}.txt".format(args.quoteasset.lower())
            filter_val = SPOT_VOLUME_FILTER_USDT_VAL
        headers = {}
        params = ()

        response = requests.get(symbol_info_api_url, headers=headers, params=params)
        json = response.json()

        lev_string_down = "DOWN{}".format(args.quoteasset)
        lev_string_up = "UP{}".format(args.quoteasset)
        symbol_list = [s["symbol"] for s in json["symbols"] if s["status"] == "TRADING" and s["quoteAsset"] == args.quoteasset and not lev_string_down in s["symbol"] and not lev_string_up in s["symbol"]]
        symbol_list.sort()

        volume_info_dict = self.get_volume_info(args)
        symbol_list = [s for s in symbol_list if volume_info_dict[s] > filter_val]

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
