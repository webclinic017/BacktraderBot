from model.reports_common import ColumnName
import pandas as pd


class Step3AvgModel(object):

    _INDEX_COLUMNS = [ColumnName.STRATEGY_ID, ColumnName.EXCHANGE, ColumnName.CURRENCY_PAIR, ColumnName.TIMEFRAME]

    def __init__(self):
        self._report_rows = []

    def add_result_row(self, run_key, analyzer_data, equity_curve_data):
        row = Step3AvgReportRow(run_key, analyzer_data, equity_curve_data)
        self._report_rows.append(row)

    def get_header_names(self):
        result = [
            ColumnName.STRATEGY_ID,
            ColumnName.EXCHANGE,
            ColumnName.CURRENCY_PAIR,
            ColumnName.TIMEFRAME,
            ColumnName.WFO_TRAINING_PERIOD,
            ColumnName.WFO_TESTING_PERIOD,
            ColumnName.TRAINING_DATE_RANGE,
            ColumnName.TESTING_DATE_RANGE,
            ColumnName.START_CASH,
            ColumnName.LOT_SIZE,
            ColumnName.TOTAL_CLOSED_TRADES,
            ColumnName.NET_PROFIT,
            ColumnName.NET_PROFIT_PCT,
            ColumnName.MAX_DRAWDOWN_PCT,
            ColumnName.MAX_DRAWDOWN_LENGTH,
            ColumnName.NET_PROFIT_TO_MAX_DRAWDOWN,
            ColumnName.WIN_RATE_PCT,
            ColumnName.EQUITY_CURVE_ANGLE,
            ColumnName.EQUITY_CURVE_R_VALUE,
            ColumnName.EQUITY_CURVE_R_SQUARED_VALUE,
            ColumnName.EQUITY_CURVE_DATA_POINTS
        ]

        return result

    def get_model_data_arr(self):
        result = []
        for row in self._report_rows:
            report_row = row.get_row_data()
            result.append(report_row)
        return result

    def get_equity_curve_model_df(self):
        df = pd.DataFrame(data=self.get_model_data_arr(), columns=self.get_header_names())
        return df.set_index(self._INDEX_COLUMNS)


class Step3AvgReportRow(object):
    def __init__(self, run_key, analyzer_data, equity_curve_data):
        self.run_key = run_key
        self.analyzer_data = analyzer_data
        self.equity_curve_data = equity_curve_data

    def get_row_data(self):
        result = [
            self.run_key.strategyid,
            self.run_key.exchange,
            self.run_key.currency_pair,
            self.run_key.timeframe,
            self.analyzer_data.wfo_training_period,
            self.analyzer_data.wfo_testing_period,
            self.analyzer_data.trainingdaterange,
            self.analyzer_data.testingdaterange,
            self.analyzer_data.startcash,
            self.analyzer_data.lot_size,
            self.analyzer_data.total_closed_trades,
            self.analyzer_data.net_profit,
            self.analyzer_data.net_profit_pct,
            self.analyzer_data.max_drawdown_pct,
            self.analyzer_data.max_drawdown_length,
            self.analyzer_data.net_profit_to_maxdd,
            self.analyzer_data.win_rate_pct,
            self.equity_curve_data.angle,
            self.equity_curve_data.rvalue,
            self.equity_curve_data.rsquaredvalue,
            self.equity_curve_data.data
        ]
        return result
