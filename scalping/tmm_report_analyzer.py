import argparse
import pandas as pd
import numpy as np
import os
import random
import re
from scalping.strategy_generator_common import ShotStrategyGenerator, TemplateTokensVO

DEFAULT_WORKING_PATH = "/Users/alex/Downloads"
DEFAULT_OUTPUT_WL_STRATEGIES_FILENAME = "algorithms.config_future_wl"

FUTURES_MAKER_FEE_PCT = 0.02
FUTURES_TAKER_FEE_PCT = 0.04
MAX_SLIPPAGE_PCT = 0.1
DEEP_LOSS_COUNT_THRESHOLD = 4

BL_FLAG_LOSS_TRADES_COUNT_THRESHOLD = 4
WL_FLAG_SYMBOL_TRADE_COUNT_THRESHOLD = 20

WL_WIN_RATE_ADDED_THRESHOLD_PCT = 4

WL_STRATEGY_DEFAULT_TEMPLATE_ID = 2
WL_STRATEGY_PARAMS_DEFAULT_ENTRY = "0.55-0.4-0.17-0.48"
WL_STRATEGY_PARAMS_REGEX = "(\d*\.?\d*)-(\d*\.?\d*)-(\d*\.?\d*)-(\d*\.?\d*)"
WL_STRATEGY_DEFAULT_ORDER_SIZE = 300

REPORT_GEN_MODE_BASE_ALL            = (0, "[Base All]")
REPORT_GEN_MODE_BASE_NO_WL          = (1, "[Base NO WL]")
REPORT_GEN_MODE_BASE_WL_ONLY        = (2, "[Base WL Only]")
REPORT_GEN_MODE_INCREMENTAL_NO_WL   = (3, "[Incremental NO WL]")
REPORT_GEN_MODE_INCREMENTAL_WL_ONLY = (4, "[Incremental WL Only]")


class TMMExcelReportAnalyzer(object):
    def __init__(self):
        self._strategy_generator = ShotStrategyGenerator()
        self._model_dict = {}
        self._total_stats_dict = {}
        self._is_incremental_mode = False
        self._incr_mode_row_count = 0
        self._is_wl_mode = False
        self._wl_mode_order_size_filter = 0
        self._wl_strategy_template_id = {}
        self._wl_strategy_params = {}
        self._wl_strategy_order_size = 0

    def parse_args(self):
        parser = argparse.ArgumentParser(description='TraderMake.Money Excel report analyzer')

        parser.add_argument('-t', '--def_tp_pct',
                            type=float,
                            required=True,
                            help=('Default TP, %'))

        parser.add_argument('-s', '--def_sl_pct',
                            type=float,
                            required=True,
                            help=('Default SL, %'))

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_input_report_filename(self):
        return '{}/report.xlsx'.format(DEFAULT_WORKING_PATH)

    def get_output_analysis_filename(self, report_gen_mode):
        if report_gen_mode == REPORT_GEN_MODE_BASE_ALL:
            return '{}/report_analysis_base_all.csv'.format(DEFAULT_WORKING_PATH)
        elif report_gen_mode == REPORT_GEN_MODE_BASE_NO_WL:
            return '{}/report_analysis_base_no_wl.csv'.format(DEFAULT_WORKING_PATH)
        elif report_gen_mode == REPORT_GEN_MODE_BASE_WL_ONLY:
            return '{}/report_analysis_base_wl_only.csv'.format(DEFAULT_WORKING_PATH)
        elif report_gen_mode == REPORT_GEN_MODE_INCREMENTAL_NO_WL:
            return '{}/report_analysis_incremental_no_wl.csv'.format(DEFAULT_WORKING_PATH)
        elif report_gen_mode == REPORT_GEN_MODE_INCREMENTAL_WL_ONLY:
            return '{}/report_analysis_incremental_wl_only.csv'.format(DEFAULT_WORKING_PATH)
        else:
            raise Exception("Wrong report_gen_mode value provided: {}".format(report_gen_mode))

    def get_output_strategy_filename(self):
            return '{}/{}'.format(DEFAULT_WORKING_PATH, DEFAULT_OUTPUT_WL_STRATEGIES_FILENAME)

    def read_report_data(self, filepath):
        try:
            df = pd.read_excel(filepath, sheet_name='Worksheet', engine='openpyxl', skiprows=7, keep_default_na=True, usecols="A:N", convert_float=False, header=None,
                               dtype={'D': np.float64, 'F': np.float64, 'I': np.float64, 'J': np.float64, 'K': np.float64, 'L': np.float64, 'M': np.float64, 'N': np.float64})
            df = df.rename(columns={0: "symbol", 1: "category", 2: "entry_timestamp", 3: "avg_entry_price", 4: "exit_timestamp", 5: "avg_exit_price", 6: "duration", 7: "side", 8: "pnl_pct", 9: "pnl_usdt", 10: "net_pnl_usdt", 11: "volume", 12: "volume_usdt", 13: "fees_usdt"})
            df = df.fillna(0)
        except Exception as e:
            return None
        return df

    def get_stats_key(self, prefix, key):
        return "{} {}".format(prefix, key)

    def user_input_incremental_mode(self):
        input_val = input("Enter last row number in Excel for incremental mode or press ENTER to skip: ")
        try:
            if input_val == "":
                print("Skipping incremental mode.")
                return

            row_number = int(input_val)
            if row_number > 0:
                self._is_incremental_mode = True
                self._incr_mode_row_count = row_number
        except Exception as e:
            print("Invalid value provided. Quitting.")
            exit(-1)

    def user_input_wl_mode(self):
        input_val = input("Enter minimum order size to select rows for white list (WL) mode or press ENTER to skip: ")
        try:
            if input_val == "":
                print("Skipping WL mode.")
                return

            order_size = int(input_val)
            if order_size > 0:
                self._is_wl_mode = True
                self._wl_mode_order_size_filter = order_size
        except Exception as e:
            print("Invalid value provided. Quitting.")
            exit(-1)

    def parse_wl_strategy_params(self, wl_strategy_params_str):
        match_obj = re.search(WL_STRATEGY_PARAMS_REGEX, wl_strategy_params_str)
        if match_obj:
            return {
                "distance": match_obj.group(1),
                "buffer": match_obj.group(2),
                "tp": match_obj.group(3),
                "sl": match_obj.group(4),
            }
        else:
            raise Exception("Wrong value provided.")

    def user_input_wl_strat_template_id(self):
        input_val = input("Enter whitelist strategy template ID (Default template ID: {}) or press ENTER to accept default: ".format(WL_STRATEGY_DEFAULT_TEMPLATE_ID))
        if input_val == "":
            print("Accepting default strategy template ID.")
            self._wl_strategy_template_id = WL_STRATEGY_DEFAULT_TEMPLATE_ID
            return
        try:
            strat_template_id = int(input_val)
            if strat_template_id > 0:
                self._wl_strategy_template_id = strat_template_id
        except Exception as e:
            print("Wrong strategy template ID.")
            exit(-1)

    def user_input_wl_strategy_params(self):
        input_val = input("Specify whitelist strategy parameters in the format: <DISTANCE>-<BUFFER>-<TP>-<SL> (Default parameters: {}) or press ENTER to accept default: ".format(WL_STRATEGY_PARAMS_DEFAULT_ENTRY))

        if input_val == "":
            self._wl_strategy_params = self.parse_wl_strategy_params(WL_STRATEGY_PARAMS_DEFAULT_ENTRY)
            return

        try:
            match_obj = re.search(WL_STRATEGY_PARAMS_REGEX, input_val)
            if match_obj:
                self._wl_strategy_params = self.parse_wl_strategy_params(input_val)
                return
            else:
                raise Exception("Wrong value provided.")

        except Exception as e:
            print("Invalid value provided. Quitting.")
            exit(-1)

    def user_input_wl_order_size(self):
        input_val = input("Enter whitelist strategy order size (Default order size: {}) or press ENTER to accept default: ".format(WL_STRATEGY_DEFAULT_ORDER_SIZE))
        if input_val == "":
            print("Accepting default order size.")
            self._wl_strategy_order_size = WL_STRATEGY_DEFAULT_ORDER_SIZE
            return
        try:
            order_size = int(input_val)
            if order_size > 0:
                self._wl_strategy_order_size = order_size
        except Exception as e:
            print("Wrong order size.")
            exit(-1)

    def get_strategy_real_win_rate_pct(self, args):
        real_tp = args.def_tp_pct - FUTURES_MAKER_FEE_PCT
        real_sl = args.def_sl_pct + FUTURES_TAKER_FEE_PCT
        return 100 * real_sl / (real_tp + real_sl)

    def calculate_trade_side_stats(self, args, df, symbol, side):
        result_dict = {}

        data_df = df[df['side'] == side]
        symbol_df = data_df[data_df['symbol'] == symbol]

        symbol_loss_trades_pnl_pct_df = symbol_df[symbol_df['pnl_pct'] < 0]
        symbol_loss_trades_net_pnl_usdt_df = symbol_df[symbol_df['net_pnl_usdt'] < 0]
        symbol_win_trades_pnl_pct_df = symbol_df[symbol_df['pnl_pct'] > 0]
        symbol_win_trades_net_pnl_usdt_df = symbol_df[symbol_df['net_pnl_usdt'] > 0]

        symbol_trade_count = len(symbol_df)
        symbol_pnl_usdt = round(symbol_df['net_pnl_usdt'].sum(), 2)
        loss_trades_count = len(symbol_df[symbol_df['net_pnl_usdt'] < 0])
        loss_trades_pct = round(100 * (loss_trades_count / symbol_trade_count), 2) if symbol_trade_count != 0 else 0
        loss_trades_pnl_pct_max = round(symbol_loss_trades_pnl_pct_df['pnl_pct'].min(), 2) if len(symbol_loss_trades_pnl_pct_df) > 0 else 0
        loss_trades_pnl_pct_avg = round(symbol_loss_trades_pnl_pct_df['pnl_pct'].mean(), 2) if len(symbol_loss_trades_pnl_pct_df) > 0 else 0
        loss_trades_net_pnl_usdt_avg = abs(symbol_loss_trades_net_pnl_usdt_df['net_pnl_usdt'].mean()) if len(symbol_loss_trades_net_pnl_usdt_df) > 0 else 0
        win_trades_count = len(symbol_df[symbol_df['net_pnl_usdt'] > 0])
        win_trades_pct = round(100 * (win_trades_count / symbol_trade_count), 2) if symbol_trade_count != 0 else 0
        win_trades_pnl_pct_max = round(symbol_win_trades_pnl_pct_df['pnl_pct'].max(), 2) if len(symbol_win_trades_pnl_pct_df) > 0 else 0
        win_trades_pnl_pct_avg = round(symbol_win_trades_pnl_pct_df['pnl_pct'].mean(), 2) if len(symbol_win_trades_pnl_pct_df) > 0 else 0
        win_trades_net_pnl_usdt_avg = abs(symbol_win_trades_net_pnl_usdt_df['net_pnl_usdt'].mean()) if len(symbol_win_trades_net_pnl_usdt_df) > 0 else 0
        expectancy_usdt = round((win_trades_count / symbol_trade_count) * win_trades_net_pnl_usdt_avg - (loss_trades_count / symbol_trade_count) * loss_trades_net_pnl_usdt_avg, 8) if symbol_trade_count != 0 else 0
        actual_rr = round(1 / (win_trades_net_pnl_usdt_avg / loss_trades_net_pnl_usdt_avg), 2) if win_trades_net_pnl_usdt_avg != 0 and loss_trades_net_pnl_usdt_avg != 0 else 0
        deep_loss_trades_count = len(symbol_df[symbol_df['pnl_pct'] < -(args.def_sl_pct + MAX_SLIPPAGE_PCT)])
        is_hollow_order_book_flag = True if deep_loss_trades_count >= DEEP_LOSS_COUNT_THRESHOLD else False
        real_win_rate_pct = self.get_strategy_real_win_rate_pct(args)
        is_blacklist_flag = True if symbol_pnl_usdt < 0 and loss_trades_count >= BL_FLAG_LOSS_TRADES_COUNT_THRESHOLD and loss_trades_pct >= (100 - real_win_rate_pct) else False
        is_final_blacklist_flag = True if is_hollow_order_book_flag or is_blacklist_flag else False
        is_whitelist_flag = True if not is_final_blacklist_flag and symbol_pnl_usdt > 0 and symbol_trade_count >= WL_FLAG_SYMBOL_TRADE_COUNT_THRESHOLD and win_trades_pct >= (real_win_rate_pct + WL_WIN_RATE_ADDED_THRESHOLD_PCT) else False

        result_dict[self.get_stats_key(side, 'symbol_trade_count')] = symbol_trade_count
        result_dict[self.get_stats_key(side, 'symbol_pnl_usdt')] = symbol_pnl_usdt
        result_dict[self.get_stats_key(side, 'expectancy_usdt')] = expectancy_usdt
        result_dict[self.get_stats_key(side, 'actual_rr')] = actual_rr
        result_dict[self.get_stats_key(side, 'loss_trades_count')] = loss_trades_count
        result_dict[self.get_stats_key(side, 'loss_trades_pct')] = loss_trades_pct
        result_dict[self.get_stats_key(side, 'loss_trades_pnl_pct_max')] = loss_trades_pnl_pct_max
        result_dict[self.get_stats_key(side, 'loss_trades_pnl_pct_avg')] = loss_trades_pnl_pct_avg
        result_dict[self.get_stats_key(side, 'win_trades_count')] = win_trades_count
        result_dict[self.get_stats_key(side, 'win_trades_pct')] = win_trades_pct
        result_dict[self.get_stats_key(side, 'win_trades_pnl_pct_max')] = win_trades_pnl_pct_max
        result_dict[self.get_stats_key(side, 'win_trades_pnl_pct_avg')] = win_trades_pnl_pct_avg
        result_dict[self.get_stats_key(side, 'deep_loss_trades_count')] = deep_loss_trades_count
        result_dict[self.get_stats_key(side, 'is_hollow_order_book_flag')] = is_hollow_order_book_flag
        result_dict[self.get_stats_key(side, 'is_blacklist_flag')] = is_blacklist_flag
        result_dict[self.get_stats_key(side, 'is_final_blacklist_flag')] = is_final_blacklist_flag
        result_dict[self.get_stats_key(side, 'is_whitelist_flag')] = is_whitelist_flag

        return result_dict

    def calculate_total_stats(self, df, model_dict, report_gen_mode):
        result_dict = {}

        long_trades_count = len(df[df['side'] == "LONG"])
        short_trades_count = len(df[df['side'] == "SHORT"])
        total_trade_count = len(df)
        long_trades_lost_count = len(df[(df['side'] == "LONG") & (df['net_pnl_usdt'] < 0)])
        long_trades_pnl_usdt = round(df[df['side'] == "LONG"]['net_pnl_usdt'].sum(), 2)
        long_trades_win_rate = round(100 * (1 - long_trades_lost_count / long_trades_count), 2) if long_trades_count > 0 else 0
        short_trades_lost_count = len(df[(df['side'] == "SHORT") & (df['net_pnl_usdt'] < 0)])
        short_trades_pnl_usdt = round(df[df['side'] == "SHORT"]['net_pnl_usdt'].sum(), 2)
        short_trades_win_rate = round(100 * (1 - short_trades_lost_count / short_trades_count), 2) if short_trades_count > 0 else 0
        loss_rate = (long_trades_lost_count + short_trades_lost_count) / total_trade_count
        win_rate = 1 - (long_trades_lost_count + short_trades_lost_count) / total_trade_count
        loss_trades_net_pnl_usdt_avg = abs(df[df['net_pnl_usdt'] < 0]['net_pnl_usdt'].mean())
        win_trades_net_pnl_usdt_avg = abs(df[df['net_pnl_usdt'] > 0]['net_pnl_usdt'].mean())
        total_pnl_usdt = round(df['net_pnl_usdt'].sum(), 2)
        expectancy_usdt = round(win_rate * win_trades_net_pnl_usdt_avg - loss_rate * loss_trades_net_pnl_usdt_avg, 4)
        actual_rr = round(1 / (win_trades_net_pnl_usdt_avg / loss_trades_net_pnl_usdt_avg), 2) if win_trades_net_pnl_usdt_avg != 0 and loss_trades_net_pnl_usdt_avg != 0 else 0
        win_rate_pct = round(100 * win_rate, 2)

        result_dict['total_trade_count'] = total_trade_count
        result_dict['long_trades_lost_count'] = long_trades_lost_count
        result_dict['long_trades_pnl_usdt'] = long_trades_pnl_usdt
        result_dict['long_trades_win_rate'] = long_trades_win_rate
        result_dict['short_trades_lost_count'] = short_trades_lost_count
        result_dict['short_trades_pnl_usdt'] = short_trades_pnl_usdt
        result_dict['short_trades_win_rate'] = short_trades_win_rate
        result_dict['total_pnl_usdt'] = total_pnl_usdt
        result_dict['expectancy_usdt'] = expectancy_usdt
        result_dict['actual_rr'] = actual_rr
        result_dict['win_rate_pct'] = win_rate_pct

        long_blacklist_arr  = [x for x in model_dict.keys() if model_dict[x]["LONG is_final_blacklist_flag"] is True]
        short_blacklist_arr = [x for x in model_dict.keys() if model_dict[x]["SHORT is_final_blacklist_flag"] is True]
        long_whitelist_arr  = [x for x in model_dict.keys() if model_dict[x]["LONG is_whitelist_flag"] is True]
        short_whitelist_arr = [x for x in model_dict.keys() if model_dict[x]["SHORT is_whitelist_flag"] is True]
        result_dict['long_blacklist_arr']  = long_blacklist_arr
        result_dict['short_blacklist_arr'] = short_blacklist_arr
        result_dict['long_whitelist_arr']  = long_whitelist_arr
        result_dict['short_whitelist_arr'] = short_whitelist_arr

        return result_dict

    def create_model(self, args, report_data_df, report_gen_mode):
        self._model_dict = {}
        self._total_stats_dict = {}

        symbol_list = report_data_df['symbol'].unique()
        symbol_list.sort()

        for symbol in symbol_list:
            row_dict = {}
            symbol_df = report_data_df[report_data_df['symbol'] == symbol]
            row_dict['total_symbol_trade_count'] = len(symbol_df)

            long_trades_stats_dict = self.calculate_trade_side_stats(args, report_data_df, symbol, "LONG")
            shorts_trades_stats_dict = self.calculate_trade_side_stats(args, report_data_df, symbol, "SHORT")
            row_dict.update(long_trades_stats_dict)
            row_dict.update({'_sep_': ""})
            row_dict.update(shorts_trades_stats_dict)
            self._model_dict[symbol] = row_dict

        self._total_stats_dict = self.calculate_total_stats(report_data_df, self._model_dict, report_gen_mode)

    def format_list(self, arr):
        return ",".join(arr)

    def compile_stats_report(self, total_stats_dict, report_gen_mode):
        if report_gen_mode == REPORT_GEN_MODE_BASE_ALL:
            stats_title = "Base ALL Statistics:"
        elif report_gen_mode == REPORT_GEN_MODE_BASE_NO_WL:
            stats_title = "Base NO WL Statistics:"
        elif report_gen_mode == REPORT_GEN_MODE_BASE_WL_ONLY:
            stats_title = "Base WL Only Statistics:"
        elif report_gen_mode == REPORT_GEN_MODE_INCREMENTAL_NO_WL:
            stats_title = "Incremental NO WL Statistics:"
        elif report_gen_mode == REPORT_GEN_MODE_INCREMENTAL_WL_ONLY:
            stats_title = "Incremental WL Only Statistics:"
        else:
            raise Exception("Wrong report_gen_mode value provided: {}".format(report_gen_mode))
        report_rows = list()
        report_rows.append([""])
        report_rows.append(["-" * 20])
        report_rows.append([stats_title])
        report_rows.append(["Trades Number:", total_stats_dict['total_trade_count']])
        report_rows.append(["LONG Trades Lost:", total_stats_dict['long_trades_lost_count']])
        report_rows.append(["LONG Trades PNL, USDT:", total_stats_dict['long_trades_pnl_usdt']])
        report_rows.append(["LONG Trades Win Rate, %:", total_stats_dict['long_trades_win_rate']])
        report_rows.append(["SHORT Trades Lost:", total_stats_dict['short_trades_lost_count']])
        report_rows.append(["SHORT Trades PNL, USDT:", total_stats_dict['short_trades_pnl_usdt']])
        report_rows.append(["SHORT Trades Win Rate, %:", total_stats_dict['short_trades_win_rate']])
        report_rows.append(["Total PnL, USDT:", total_stats_dict['total_pnl_usdt']])
        report_rows.append(["Trading Expectancy, USDT:", total_stats_dict['expectancy_usdt']])
        report_rows.append(["Real RR (1/R:R):", "{}".format(total_stats_dict['actual_rr'])])
        report_rows.append(["Total Win Rate, %:", total_stats_dict['win_rate_pct']])
        if report_gen_mode == REPORT_GEN_MODE_BASE_ALL:
            report_rows.append([""])
            report_rows.append(["LONG Blacklist:",  self.format_list(total_stats_dict['long_blacklist_arr']) if total_stats_dict['long_blacklist_arr'] else ""])
            report_rows.append(["SHORT Blacklist:", self.format_list(total_stats_dict['short_blacklist_arr'])if total_stats_dict['short_blacklist_arr'] else ""])
            report_rows.append(["LONG Whitelist:",  self.format_list(total_stats_dict['long_whitelist_arr']) if total_stats_dict['long_whitelist_arr'] else ""])
            report_rows.append(["SHORT Whitelist:", self.format_list(total_stats_dict['short_whitelist_arr'])if total_stats_dict['short_whitelist_arr'] else ""])

        return report_rows

    def write_analysis_report(self, stats_report_rows, report_gen_mode):
        if len(self._model_dict) == 0:
            return

        report_rows = []
        report_header_row = []
        for symbol, stats in self._model_dict.items():
            report_header_row = stats.keys()
            row = [symbol]
            row.extend(stats.values())
            report_rows.append(row)

        report_rows.extend(stats_report_rows)

        header = ['symbol']
        header.extend(report_header_row)

        report_filename = self.get_output_analysis_filename(report_gen_mode)
        df = pd.DataFrame(report_rows, columns=header).set_index('symbol')
        df.to_csv(report_filename)

        print("Saved report analysis file: {}\n".format(report_filename))

    def generate_whitelist_strategies(self, strat_template_id, total_stats_dict, wl_strategy_params, wl_order_size):
        long_whitelist = total_stats_dict['long_whitelist_arr']
        short_whitelist = total_stats_dict['short_whitelist_arr']

        if not long_whitelist and not short_whitelist:
            return

        combined_list = []
        for symbol in long_whitelist:
            combined_list.append([symbol, "LONG"])

        for symbol in short_whitelist:
            combined_list.append([symbol, "SHORT"])

        df = pd.DataFrame(combined_list)
        df = df.sort_values(by=[0, 1], ascending=True)

        strategy_template = self._strategy_generator.read_strategy_template(False, strat_template_id)
        strategy_list = []
        for idx, row in df.iterrows():
            tokens_vo = TemplateTokensVO()
            tokens_vo.symbol_name = row[0]
            tokens_vo.shot_type = row[1]
            tokens_vo.distance = wl_strategy_params["distance"]
            tokens_vo.buffer = wl_strategy_params["buffer"]
            tokens_vo.tp = wl_strategy_params["tp"]
            tokens_vo.sl = wl_strategy_params["sl"]

            is_last = idx == df.index[-1]
            strategy_list.append(self._strategy_generator.generate_strategy(False, True, strategy_template, tokens_vo, wl_order_size, is_last, "**WL**"))
        strategy_list_str = ''.join(strategy_list)

        final_content = self._strategy_generator.generate_final_content(strategy_list_str, False, True)
        out_filename = self.get_output_strategy_filename()
        self._strategy_generator.write_file(out_filename, final_content)

        print("\nStrategy file {} has been generated!".format(out_filename))

    def generate_report(self, args, df, report_gen_mode):
        if report_gen_mode == REPORT_GEN_MODE_BASE_ALL:
            report_df = df
        elif report_gen_mode == REPORT_GEN_MODE_BASE_NO_WL:
            report_df = df[df['volume_usdt'] < self._wl_mode_order_size_filter] if self._is_wl_mode else df
        elif report_gen_mode == REPORT_GEN_MODE_BASE_WL_ONLY:
            report_df = df[df['volume_usdt'] > self._wl_mode_order_size_filter] if self._is_wl_mode else df
        elif report_gen_mode == REPORT_GEN_MODE_INCREMENTAL_NO_WL:
            report_df = df.head(self._incr_mode_row_count)
            report_df = report_df[report_df['volume_usdt'] < self._wl_mode_order_size_filter] if self._is_wl_mode else report_df
        elif report_gen_mode == REPORT_GEN_MODE_INCREMENTAL_WL_ONLY:
            report_df = df.head(self._incr_mode_row_count)
            report_df = report_df[report_df['volume_usdt'] > self._wl_mode_order_size_filter] if self._is_wl_mode else report_df
        else:
            raise Exception("Wrong report_gen_mode value provided: {}".format(report_gen_mode))
        if len(report_df) > 0:
            print("Processing {} mode ...".format(report_gen_mode[1]))
            self.create_model(args, report_df, report_gen_mode)
            stats_report_rows = self.compile_stats_report(self._total_stats_dict, report_gen_mode)
            self.write_analysis_report(stats_report_rows, report_gen_mode)
        else:
            print("There is no data to process {} mode!".format(report_gen_mode[1]))

    def run(self):
        random.seed()
        args = self.parse_args()

        filename = self.get_input_report_filename()
        report_data_df = self.read_report_data(filename)
        if report_data_df is None or report_data_df.empty:
            print("*** No TraderMake.Money Excel report data found! Quitting.")
            exit(-1)

        self.user_input_incremental_mode()
        self.user_input_wl_mode()
        if self._is_wl_mode:
            self.user_input_wl_strat_template_id()
            self.user_input_wl_strategy_params()
            self.user_input_wl_order_size()

        self.generate_report(args, report_data_df, REPORT_GEN_MODE_BASE_ALL)
        if self._is_wl_mode:
            self.generate_whitelist_strategies(self._wl_strategy_template_id, self._total_stats_dict, self._wl_strategy_params, self._wl_strategy_order_size)

        if self._is_wl_mode:
            self.generate_report(args, report_data_df, REPORT_GEN_MODE_BASE_NO_WL)
            self.generate_report(args, report_data_df, REPORT_GEN_MODE_BASE_WL_ONLY)

        if self._is_incremental_mode:
            self.generate_report(args, report_data_df, REPORT_GEN_MODE_INCREMENTAL_NO_WL)

            if self._is_wl_mode:
                self.generate_report(args, report_data_df, REPORT_GEN_MODE_INCREMENTAL_WL_ONLY)


def main():
    step = TMMExcelReportAnalyzer()
    step.run()


if __name__ == '__main__':
    main()
