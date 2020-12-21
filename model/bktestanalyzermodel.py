
from model.reports_common import ColumnName


class BktestAnalyzerModel(object):
    def __init__(self):
        self._report_rows = []

    def add_result_row(self, run_key, analyzer_data, equity_curve_data, montecarlo_data, bktestanalyzergrouping_data):
        row = BktestAnalyzerReportRow(run_key, analyzer_data, equity_curve_data, montecarlo_data, bktestanalyzergrouping_data)
        self._report_rows.append(row)

    def get_header_names(self):
        result = [
            ColumnName.STRATEGY_ID,
            ColumnName.EXCHANGE,
            ColumnName.CURRENCY_PAIR,
            ColumnName.TIMEFRAME,
            ColumnName.PARAMETERS_GROUPING_KEY,
            ColumnName.PARAMETERS_BEST_RECORD_IN_GROUP,
            ColumnName.TOTAL_CLOSED_TRADES,
            ColumnName.TRADES_NUM_SL_COUNT,
            ColumnName.TRADES_NUM_TSL_COUNT,
            ColumnName.TRADES_NUM_TP_COUNT,
            ColumnName.TRADES_NUM_TTP_COUNT,
            ColumnName.TRADES_NUM_TB_COUNT,
            ColumnName.TRADES_NUM_DCA_TRIGGERED_COUNT,
            ColumnName.NET_PROFIT,
            ColumnName.MAX_DRAWDOWN_PCT,
            ColumnName.MAX_DRAWDOWN_LENGTH,
            ColumnName.NET_PROFIT_TO_MAX_DRAWDOWN,
            ColumnName.WIN_RATE_PCT,
            ColumnName.PROFIT_FACTOR,
            ColumnName.EQUITY_CURVE_R_VALUE,
            ColumnName.EQUITY_CURVE_R_SQUARED_VALUE,
            ColumnName.MC_RISK_OF_RUIN_PCT,
            ColumnName.TOTAL_ROWS,
            ColumnName.AVG_NET_PROFIT_PCT,
            ColumnName.BACKTESTING_PROFITABLE_RECORDS,
            ColumnName.BACKTESTING_PROFITABLE_RECORDS_PCT
        ]
        return result

    def get_model_data_arr(self):
        result = []
        for row in self._report_rows:
            report_row = row.get_row_data()
            result.append(report_row)
        return result


class BktestAnalyzerReportRow(object):
    def __init__(self, run_key, analyzer_data, equity_curve_data, montecarlo_data, bktestanalyzergrouping_data):
        self.run_key = run_key
        self.analyzer_data = analyzer_data
        self.equity_curve_data = equity_curve_data
        self.montecarlo_data = montecarlo_data
        self.bktestanalyzergrouping_data = bktestanalyzergrouping_data

    def get_row_data(self):
        result = [
            self.run_key.strategyid,
            self.run_key.exchange,
            self.run_key.currency_pair,
            self.run_key.timeframe,
            self.bktestanalyzergrouping_data.parameters_grouping_key,
            self.bktestanalyzergrouping_data.parameters_best_record_in_group,
            self.analyzer_data.total_closed_trades,
            self.analyzer_data.sl_trades_count,
            self.analyzer_data.tsl_trades_count,
            self.analyzer_data.tp_trades_count,
            self.analyzer_data.ttp_trades_count,
            self.analyzer_data.tb_trades_count,
            self.analyzer_data.dca_triggered_count,
            self.analyzer_data.net_profit_pct,
            self.analyzer_data.max_drawdown_pct,
            self.analyzer_data.max_drawdown_length,
            self.analyzer_data.net_profit_to_maxdd,
            self.analyzer_data.win_rate_pct,
            self.analyzer_data.profit_factor,
            self.equity_curve_data.equitycurvervalue,
            self.equity_curve_data.equitycurversquaredvalue,
            self.montecarlo_data.mc_riskofruin_pct,
            self.bktestanalyzergrouping_data.total_rows,
            self.bktestanalyzergrouping_data.avg_net_profit_pct,
            self.bktestanalyzergrouping_data.bktest_profitable_records_num,
            self.bktestanalyzergrouping_data.bktest_profitable_records_pct
        ]
        return result
