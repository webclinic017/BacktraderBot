
from datetime import date
from calendar import monthrange


class BacktestAnalyzerModel(object):
    def __init__(self):
        self._report_rows = []

    def add_result_row(self, strategyid, exchange, currency_pair, timeframe, parameters, parameters_best_record, total_closed_trades, sl_trades_count, tsl_trades_count, tp_trades_count, ttp_trades_count,
                 tb_trades_count, dca_triggered_count, net_profit_pct, max_drawdown_pct, max_drawdown_length, win_rate_pct, profit_factor, equitycurvervalue, total_rows, avg_net_profit_pct,
                 bktest_profitable_records_num, bktest_profitable_records_pct, fwtest_total_closed_trades, fwtest_net_profit_pct, fwtest_profitable_records_num, fwtest_profitable_records_pct):
        row = BacktestAnalyzerReportRow(strategyid, exchange, currency_pair, timeframe, parameters, parameters_best_record, total_closed_trades, sl_trades_count, tsl_trades_count, tp_trades_count, ttp_trades_count,
                 tb_trades_count, dca_triggered_count, net_profit_pct, max_drawdown_pct, max_drawdown_length, win_rate_pct, profit_factor, equitycurvervalue, total_rows, avg_net_profit_pct,
                 bktest_profitable_records_num, bktest_profitable_records_pct, fwtest_total_closed_trades, fwtest_net_profit_pct, fwtest_profitable_records_num, fwtest_profitable_records_pct)
        self._report_rows.append(row)

    def get_header_names(self):
        result = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters Grouping Key', 'Parameters - Best Record In Group', 'Total Closed Trades', 'Trades # SL Count',
                  'Trades # TSL Count', 'Trades # TP Count', 'Trades # TTP Count', 'Trades # TB Count', 'Trades # DCA Triggered Count', 'Net Profit, %',
                  'Max Drawdown, %', 'Max Drawdown Length', 'Win Rate, %', 'Profit Factor', 'Equity Curve R-value', 'Total Rows', 'Avg. Net Profit, %',
                  'BkTest Profitable Records', 'BkTest Profitable Records, %',
                  'FwTest: Total Closed Trades', 'FwTest: Net Profit, %', 'FwTest Profitable Records', 'FwTest Profitable Records, %']
        return result

    def get_model_data_arr(self):
        result = []
        for row in self._report_rows:
            report_row = row.get_row_data()
            result.append(report_row)
        return result


class BacktestAnalyzerReportRow(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe, parameters, parameters_best_record, total_closed_trades, sl_trades_count, tsl_trades_count, tp_trades_count, ttp_trades_count,
                 tb_trades_count, dca_triggered_count, net_profit_pct, max_drawdown_pct, max_drawdown_length, win_rate_pct, profit_factor, equitycurvervalue, total_rows, avg_net_profit_pct,
                 bktest_profitable_records_num, bktest_profitable_records_pct, fwtest_total_closed_trades, fwtest_net_profit_pct, fwtest_profitable_records_num, fwtest_profitable_records_pct):
        self.strategyid = strategyid
        self.exchange = exchange
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.parameters = parameters
        self.parameters_best_record = parameters_best_record
        self.total_closed_trades = total_closed_trades
        self.sl_trades_count = sl_trades_count
        self.tsl_trades_count = tsl_trades_count
        self.tp_trades_count = tp_trades_count
        self.ttp_trades_count = ttp_trades_count
        self.tb_trades_count = tb_trades_count
        self.dca_triggered_count = dca_triggered_count
        self.net_profit_pct = net_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_drawdown_length = max_drawdown_length
        self.win_rate_pct = win_rate_pct
        self.profit_factor = profit_factor
        self.equitycurvervalue = equitycurvervalue
        self.total_rows = total_rows
        self.avg_net_profit_pct = avg_net_profit_pct
        self.bktest_profitable_records_num = bktest_profitable_records_num
        self.bktest_profitable_records_pct = bktest_profitable_records_pct
        self.fwtest_total_closed_trades = fwtest_total_closed_trades
        self.fwtest_net_profit_pct = fwtest_net_profit_pct
        self.fwtest_profitable_records_num = fwtest_profitable_records_num
        self.fwtest_profitable_records_pct = fwtest_profitable_records_pct

    def get_row_data(self):
        result = [
            self.strategyid,
            self.exchange,
            self.currency_pair,
            self.timeframe,
            self.parameters,
            self.parameters_best_record,
            self.total_closed_trades,
            self.sl_trades_count,
            self.tsl_trades_count,
            self.tp_trades_count,
            self.ttp_trades_count,
            self.tb_trades_count,
            self.dca_triggered_count,
            self.net_profit_pct,
            self.max_drawdown_pct,
            self.max_drawdown_length,
            self.win_rate_pct,
            self.profit_factor,
            self.equitycurvervalue,
            self.total_rows,
            self.avg_net_profit_pct,
            self.bktest_profitable_records_num,
            self.bktest_profitable_records_pct,
            self.fwtest_total_closed_trades,
            self.fwtest_net_profit_pct,
            self.fwtest_profitable_records_num,
            self.fwtest_profitable_records_pct
        ]
        return result


