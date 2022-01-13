import argparse
import pandas as pd
import os
import random
import fdb
import datetime as dt

DEFAULT_WORKING_PATH = "c:/Python/Scalping"
FDB_REPORT_FILENAME = "c:/MoonTrader/data/mt-core/mtdb022.fdb"

MAX_SLIPPAGE_PCT = 50

BL_FLAG_CRIT1_SYMBOL_TRADES_SS_COUNT = 7
BL_FLAG_CRIT1_WIN_RATE_PCT = 60
BL_FLAG_CRIT2_ALL_LOSS_TRADES_MIN_COUNT = 4
BL_FLAG_CRIT2_ALL_LOSS_TRADES_MAX_COUNT = 6
BL_FLAG_CRIT3_DEEP_LOSS_TRADES_COUNT = 2
WL_FLAG_CRIT1_SYMBOL_TRADE_SS_COUNT = 20
WL_FLAG_CRIT1_SYMBOL_WIN_RATE_PCT = 80

REPORT_GEN_MODE_ALL = (0, "[All]")

IS_PRINT_ALL_TRADES_FLAG = True

DEFAULT_LEVERAGE = 5


class MTReportAnalyzer(object):
    def __init__(self):
        self._model_dict = {}
        self._total_stats_dict = {}

    def parse_args(self):
        parser = argparse.ArgumentParser(description='MT report analyzer')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_report_db_filename(self):
        return FDB_REPORT_FILENAME

    def get_trades_filename(self):
        curr_dt = dt.datetime.now().strftime("%Y%m%d_%H%M")
        return '{}/{}-all-trades.xlsx'.format(DEFAULT_WORKING_PATH, curr_dt)

    def get_output_analysis_filename(self, report_gen_mode, strategy_id):
        if report_gen_mode == REPORT_GEN_MODE_ALL:
            curr_dt = dt.datetime.now().strftime("%Y%m%d_%H%M")
            return '{}/{}-report-{}.xlsx'.format(DEFAULT_WORKING_PATH, curr_dt, strategy_id)
        else:
            raise Exception("Wrong report_gen_mode value provided: {}".format(report_gen_mode))

    def read_report_data(self, db_filename):
        try:
            fdb.load_api('C:/Program Files/Firebird/Firebird_3_0/fbclient.dll')
            conn = fdb.connect(dsn=db_filename, user='sysdba', password='masterkey',
                              fb_library_name='C:/Program Files/Firebird/Firebird_3_0/fbclient.dll',
                              sql_dialect=1,  # necessary for all dialect 1 databases
                              charset='UTF8'  # specify a character set for the connection
            )

            cur = conn.cursor()
            SELECT = """ SELECT 
                        rd.REPORT_TIMESTAMP,
                        UPPER(rd.SYMBOL),
                        (SELECT 
                         mt.NAME 
                         FROM
                         MARKET_TYPE mt
                         WHERE
                         mt.ID = rd.FK_MARKET_TYPE) AS market_type,
                        rd.PRICE_OPEN,
                        rd.PRICE_CLOSE,
                        rd.QTY,
                        rd.EXECUTED_QTY,
                        (SELECT
                         (case when ost.ID = 1 then "LONG"
                               when ost.ID = -1 then "SHORT"
                               else ost.NAME
                          end)
                         FROM
                         ORDER_SIDE_TYPE ost
                         WHERE
                         ost.ID = rd.FK_ORDER_SIDE_TYPE) AS order_side_type,
                        rd.PROFIT,
                        rd.PROFIT_PERCENTAGE,
                        rd.COMMISSION_USDT,
                        rd.PROFIT_USDT,
                        rd.EXECUTED_QTY_USDT,
                        rd.TOTAL_USDT,
                        rd.COMMENT
                    FROM REPORT_DATA rd
                    WHERE
                    rd.IS_DELETED = False
                    ORDER BY
                    rd.REPORT_TIMESTAMP
                    """

            cur.execute(SELECT)

            data = cur.fetchall()
            df = pd.DataFrame(data, columns=["entry_timestamp", "symbol", "market_type", "avg_entry_price", "avg_exit_price", "qty", "executed_qty", "side", "profit", "pnl_pct", "fees_usdt", "pnl_usdt", "volume_usdt", "net_pnl_usdt", "strategy_id"])
            df = df.fillna(0)
            for i in range(len(df)):
                strat_id = df['strategy_id'].values[i]
                if "Info:" in strat_id:
                    strat_id = strat_id[strat_id.index("Info:") + 6 : ]
                df['strategy_id'].values[i] = strat_id
            if IS_PRINT_ALL_TRADES_FLAG:
                df.to_excel(self.get_trades_filename(), engine='xlsxwriter')
        except Exception as e:
            raise Exception("Error during connecting to FDB database: {}".format(e))
        return df

    def get_stats_key(self, side, key):
        prefix = "NA"
        if side == "LONG":
            prefix = "L"
        elif side == "SHORT":
            prefix = "S"

        return "{} {}".format(prefix, key)

    def get_max_loss_streak(self, df):
        curr_loss_count = 0
        max_loss_count = 0
        for net_pnl in df['net_pnl_usdt']:
            if net_pnl < 0:
                curr_loss_count += 1
                max_loss_count = max(curr_loss_count, max_loss_count)
            if net_pnl > 0:
                curr_loss_count = 0
        return max_loss_count

    def get_max_win_streak(self, df):
        curr_win_count = 0
        max_win_count = 0
        for net_pnl in df['net_pnl_usdt']:
            if net_pnl > 0:
                curr_win_count += 1
                max_win_count = max(curr_win_count, max_win_count)
            if net_pnl < 0:
                curr_win_count = 0
        return max_win_count

    def get_max_drawdown_pct(self, initial_capital, df):
        maxportfoliovalue = tradeclosevalue = initial_capital
        max_moneydown = 0
        max_drawdown_pct = 0
        if len(df) == 0:
            return 0
        for net_pnl in df['net_pnl_usdt']:
            tradeclosevalue = tradeclosevalue + net_pnl
            if tradeclosevalue < maxportfoliovalue:
                moneydown = tradeclosevalue - maxportfoliovalue
                drawdown_pct = 100.0 * moneydown / maxportfoliovalue
            else:
                maxportfoliovalue = tradeclosevalue
                moneydown = 0
                drawdown_pct = 0

            # maximum drawdown values
            max_moneydown = min(max_moneydown, moneydown)
            max_drawdown_pct = min(max_drawdown_pct, drawdown_pct)

        return max_drawdown_pct

    def is_bl_condition(self, symbol_pnl_usdt, symbol_trade_count, loss_trades_count, win_trades_pct, deep_loss_trades_count):
        criterion1_flag = symbol_pnl_usdt < 0 and symbol_trade_count >= BL_FLAG_CRIT1_SYMBOL_TRADES_SS_COUNT and win_trades_pct < BL_FLAG_CRIT1_WIN_RATE_PCT
        criterion2_flag = symbol_pnl_usdt < 0 and loss_trades_count >= BL_FLAG_CRIT2_ALL_LOSS_TRADES_MIN_COUNT and loss_trades_count <= BL_FLAG_CRIT2_ALL_LOSS_TRADES_MAX_COUNT and win_trades_pct == 0
        criterion3_flag = symbol_pnl_usdt < 0 and deep_loss_trades_count >= BL_FLAG_CRIT3_DEEP_LOSS_TRADES_COUNT
        return criterion1_flag or criterion2_flag or criterion3_flag

    def is_wl_condition(self, symbol_pnl_usdt, symbol_trade_count, win_trades_pct):
        criterion1_flag = symbol_pnl_usdt > 0 and symbol_trade_count >= WL_FLAG_CRIT1_SYMBOL_TRADE_SS_COUNT and win_trades_pct >= WL_FLAG_CRIT1_SYMBOL_WIN_RATE_PCT
        return criterion1_flag

    def calculate_trade_side_stats(self, df, symbol, side, deposit_size):
        result_dict = {}

        data_df = df[df['side'] == side]
        symbol_df = data_df[data_df['symbol'] == symbol]

        all_symbols_loss_trades_pnl_pct_df = data_df[data_df['pnl_pct'] < 0]
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
        max_loss_streak = self.get_max_loss_streak(symbol_df)
        win_trades_count = len(symbol_df[symbol_df['net_pnl_usdt'] > 0])
        win_trades_pct = round(100 * (win_trades_count / symbol_trade_count), 2) if symbol_trade_count != 0 else 0
        win_trades_pnl_pct_max = round(symbol_win_trades_pnl_pct_df['pnl_pct'].max(), 2) if len(symbol_win_trades_pnl_pct_df) > 0 else 0
        win_trades_pnl_pct_avg = round(symbol_win_trades_pnl_pct_df['pnl_pct'].mean(), 2) if len(symbol_win_trades_pnl_pct_df) > 0 else 0
        win_trades_net_pnl_usdt_avg = abs(symbol_win_trades_net_pnl_usdt_df['net_pnl_usdt'].mean()) if len(symbol_win_trades_net_pnl_usdt_df) > 0 else 0
        max_win_streak = self.get_max_win_streak(symbol_df)
        max_drawdown_pct = round(self.get_max_drawdown_pct(deposit_size, symbol_df), 2)
        loss_all_trades_pnl_pct_avg = round(all_symbols_loss_trades_pnl_pct_df['pnl_pct'].mean(), 2) if len(all_symbols_loss_trades_pnl_pct_df) > 0 else 0
        deep_loss_trades_count = len(symbol_df[symbol_df['pnl_pct'] < loss_all_trades_pnl_pct_avg * (1 + MAX_SLIPPAGE_PCT / 100)])
        expectancy_usdt = round((win_trades_count / symbol_trade_count) * win_trades_net_pnl_usdt_avg - (loss_trades_count / symbol_trade_count) * loss_trades_net_pnl_usdt_avg, 4) if symbol_trade_count != 0 else 0
        expectancy_pct = "{}%".format(round(100 * expectancy_usdt / symbol_df['volume_usdt'].mean(), 2)) if expectancy_usdt != 0 else 0
        is_blacklist_flag = self.is_bl_condition(symbol_pnl_usdt, symbol_trade_count, loss_trades_count, win_trades_pct, deep_loss_trades_count)
        is_whitelist_flag = self.is_wl_condition(symbol_pnl_usdt, symbol_trade_count, win_trades_pct)

        result_dict[self.get_stats_key(side, 'symbol_trade_count')] = symbol_trade_count
        result_dict[self.get_stats_key(side, 'symbol_pnl_usdt')] = symbol_pnl_usdt
        result_dict[self.get_stats_key(side, 'expectancy_usdt')] = expectancy_usdt
        result_dict[self.get_stats_key(side, 'expectancy_pct')] = expectancy_pct
        result_dict[self.get_stats_key(side, 'loss_trades_count')] = loss_trades_count
        result_dict[self.get_stats_key(side, 'loss_trades_pct')] = loss_trades_pct
        result_dict[self.get_stats_key(side, 'loss_trades_pnl_pct_max')] = loss_trades_pnl_pct_max
        result_dict[self.get_stats_key(side, 'loss_trades_pnl_pct_avg')] = loss_trades_pnl_pct_avg
        result_dict[self.get_stats_key(side, 'max_loss_streak')] = max_loss_streak
        result_dict[self.get_stats_key(side, 'win_trades_count')] = win_trades_count
        result_dict[self.get_stats_key(side, 'win_trades_pct')] = win_trades_pct
        result_dict[self.get_stats_key(side, 'win_trades_pnl_pct_max')] = win_trades_pnl_pct_max
        result_dict[self.get_stats_key(side, 'win_trades_pnl_pct_avg')] = win_trades_pnl_pct_avg
        result_dict[self.get_stats_key(side, 'deep_loss_trades_count')] = deep_loss_trades_count
        result_dict[self.get_stats_key(side, 'max_win_streak')] = max_win_streak
        result_dict[self.get_stats_key(side, 'max_drawdown_pct')] = max_drawdown_pct
        result_dict[self.get_stats_key(side, 'is_blacklist_flag')] = is_blacklist_flag
        result_dict[self.get_stats_key(side, 'is_whitelist_flag')] = is_whitelist_flag

        return result_dict

    def calculate_total_stats(self, df, model_dict, deposit_size, avg_order_size):
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
        total_pnl_pct = round(100 * df['net_pnl_usdt'].sum() / deposit_size, 2)
        expectancy_usdt = round(win_rate * win_trades_net_pnl_usdt_avg - loss_rate * loss_trades_net_pnl_usdt_avg, 4)
        expectancy_pct = "{}%".format(round(100 * expectancy_usdt / df['volume_usdt'].mean(), 2)) if expectancy_usdt != 0 else 0
        max_loss_streak = self.get_max_loss_streak(df)
        max_win_streak = self.get_max_win_streak(df)
        max_drawdown_pct = round(self.get_max_drawdown_pct(deposit_size, df), 2)
        recovery_factor_pct = round(total_pnl_pct / max_drawdown_pct, 2)

        result_dict['total_trade_count'] = total_trade_count
        result_dict['long_trades_lost_count'] = long_trades_lost_count
        result_dict['long_trades_pnl_usdt'] = long_trades_pnl_usdt
        result_dict['long_trades_win_rate'] = long_trades_win_rate
        result_dict['short_trades_lost_count'] = short_trades_lost_count
        result_dict['short_trades_pnl_usdt'] = short_trades_pnl_usdt
        result_dict['short_trades_win_rate'] = short_trades_win_rate
        result_dict['total_pnl_usdt'] = total_pnl_usdt
        result_dict['total_pnl_pct'] = total_pnl_pct
        result_dict['expectancy_usdt'] = expectancy_usdt
        result_dict['expectancy_pct'] = expectancy_pct
        result_dict['max_loss_streak'] = max_loss_streak
        result_dict['max_win_streak'] = max_win_streak
        result_dict['deposit_size'] = round(deposit_size, 2)
        result_dict['avg_order_size'] = round(avg_order_size, 2)
        result_dict['max_drawdown_pct'] = max_drawdown_pct
        result_dict['recovery_factor_pct'] = recovery_factor_pct
        result_dict['actual_win_rate_pct'] = round(100 * win_rate, 2)

        long_blacklist_arr  = [x for x in model_dict.keys() if model_dict[x]["L is_blacklist_flag"] is True]
        short_blacklist_arr = [x for x in model_dict.keys() if model_dict[x]["S is_blacklist_flag"] is True]
        long_whitelist_arr  = [x for x in model_dict.keys() if model_dict[x]["L is_whitelist_flag"] is True]
        short_whitelist_arr = [x for x in model_dict.keys() if model_dict[x]["S is_whitelist_flag"] is True]
        result_dict['long_blacklist_arr']  = long_blacklist_arr
        result_dict['short_blacklist_arr'] = short_blacklist_arr
        result_dict['long_whitelist_arr']  = long_whitelist_arr
        result_dict['short_whitelist_arr'] = short_whitelist_arr

        return result_dict

    def create_model(self, report_data_df):
        self._model_dict = {}
        self._total_stats_dict = {}

        deposit_size = self.get_deposit_size(report_data_df)
        avg_order_size = self.get_avg_order_size(report_data_df)

        symbol_list = report_data_df['symbol'].unique()
        symbol_list.sort()

        for symbol in symbol_list:
            row_dict = {}
            symbol_df = report_data_df[report_data_df['symbol'] == symbol]
            row_dict['total_symbol_trade_count'] = len(symbol_df)

            long_trades_stats_dict = self.calculate_trade_side_stats(report_data_df, symbol, "LONG", deposit_size)
            shorts_trades_stats_dict = self.calculate_trade_side_stats(report_data_df, symbol, "SHORT", deposit_size)
            row_dict.update(long_trades_stats_dict)
            row_dict.update({'_sep_': ""})
            row_dict.update(shorts_trades_stats_dict)
            self._model_dict[symbol] = row_dict

        self._total_stats_dict = self.calculate_total_stats(report_data_df, self._model_dict, deposit_size, avg_order_size)

    def format_list(self, arr):
        return ",".join(arr)

    def compile_stats_report(self, strategy_id, total_stats_dict, report_gen_mode):
        if report_gen_mode == REPORT_GEN_MODE_ALL:
            stats_title = "ALL Statistics:"
        else:
            raise Exception("Wrong report_gen_mode value provided: {}".format(report_gen_mode))
        report_rows = list()
        report_rows.append([""])
        report_rows.append([strategy_id])
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
        report_rows.append(["Trading Expectancy, %:", total_stats_dict['expectancy_pct']])
        report_rows.append(["Max Loss Streak:", total_stats_dict['max_loss_streak']])
        report_rows.append(["Max Win Streak:", total_stats_dict['max_win_streak']])
        report_rows.append(["Deposit Size:", total_stats_dict['deposit_size']])
        report_rows.append(["Average Order Size:", total_stats_dict['avg_order_size']])
        report_rows.append(["Maximum Drawdown, %:", total_stats_dict['max_drawdown_pct']])
        report_rows.append(["Actual Win Rate, %:", total_stats_dict['actual_win_rate_pct']])
        if report_gen_mode == REPORT_GEN_MODE_ALL:
            report_rows.append([""])
            report_rows.append(["LONG Blacklist:",  self.format_list(total_stats_dict['long_blacklist_arr']) if total_stats_dict['long_blacklist_arr'] else ""])
            report_rows.append(["SHORT Blacklist:", self.format_list(total_stats_dict['short_blacklist_arr'])if total_stats_dict['short_blacklist_arr'] else ""])
            report_rows.append(["LONG Whitelist:",  self.format_list(total_stats_dict['long_whitelist_arr']) if total_stats_dict['long_whitelist_arr'] else ""])
            report_rows.append(["SHORT Whitelist:", self.format_list(total_stats_dict['short_whitelist_arr'])if total_stats_dict['short_whitelist_arr'] else ""])

        return report_rows

    def write_analysis_report(self, stats_report_rows, report_gen_mode, strategy_id):
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

        report_filename = self.get_output_analysis_filename(report_gen_mode, strategy_id)
        df = pd.DataFrame(report_rows, columns=header).set_index('symbol')
        df.to_excel(report_filename, engine='xlsxwriter')

        print("Saved report analysis file: {}\n".format(report_filename))

    def get_avg_order_size(self, df):
        return df['volume_usdt'].mean()

    def get_deposit_size(self, df):
        return self.get_avg_order_size(df) / DEFAULT_LEVERAGE

    def get_report_strategies_list(self, df):
        s_list = df['strategy_id'].unique()
        s_list.sort()
        return list(s_list)

    def generate_report(self, df, report_gen_mode):
        if report_gen_mode == REPORT_GEN_MODE_ALL:
            report_df = df
        else:
            raise Exception("Wrong report_gen_mode value provided: {}".format(report_gen_mode))
        if len(report_df) > 0:
            print("Processing {} mode ...".format(report_gen_mode[1]))
            strategies_list = self.get_report_strategies_list(report_df)
            for strategy_id in strategies_list:
                strat_df = report_df.loc[report_df['strategy_id'] == strategy_id]
                self.create_model(strat_df)
                stats_report_rows = self.compile_stats_report(strategy_id, self._total_stats_dict, report_gen_mode)
                self.write_analysis_report(stats_report_rows, report_gen_mode, strategy_id)
        else:
            print("There is no data to process {} mode!".format(report_gen_mode[1]))

    def run(self):
        random.seed()
        args = self.parse_args()

        db_filename = self.get_report_db_filename()
        report_data_df = self.read_report_data(db_filename)
        if report_data_df is None or report_data_df.empty:
            print("*** No report data found! Quitting.")
            exit(-1)

        self.generate_report(report_data_df, REPORT_GEN_MODE_ALL)


def main():
    step = MTReportAnalyzer()
    step.run()


if __name__ == '__main__':
    main()
