from model.reports_common import ColumnName
import pandas as pd


class Step3Model(object):

    _INDEX_COLUMNS = [ColumnName.STRATEGY_ID, ColumnName.EXCHANGE, ColumnName.CURRENCY_PAIR, ColumnName.TIMEFRAME]

    def __init__(self):
        self._report_rows = []
        self._equity_curve_report_rows = []

    def add_result_row(self, run_key, analyzer_data, equity_curve_data, montecarlo_data):
        row = Step3ReportRow(run_key, analyzer_data, equity_curve_data, montecarlo_data)
        self._report_rows.append(row)

    def get_header_names(self):
        result = [
            ColumnName.STRATEGY_ID,
            ColumnName.EXCHANGE,
            ColumnName.CURRENCY_PAIR,
            ColumnName.TIMEFRAME,
            ColumnName.PARAMETERS,
            ColumnName.WFO_CYCLE_TRAINING_ID,
            ColumnName.WFO_TRAINING_PERIOD,
            ColumnName.WFO_TESTING_PERIOD,
            ColumnName.TRAINING_DATE_RANGE,
            ColumnName.TESTING_DATE_RANGE,
            ColumnName.NUM_WFO_CYCLES,
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
            ColumnName.EQUITY_CURVE_SLOPE,
            ColumnName.EQUITY_CURVE_INTERCEPT,
            ColumnName.EQUITY_CURVE_R_VALUE,
            ColumnName.EQUITY_CURVE_R_SQUARED_VALUE,
            ColumnName.EQUITY_CURVE_P_VALUE,
            ColumnName.EQUITY_CURVE_STDERR,
            ColumnName.MC_RISK_OF_RUIN_PCT,
            ColumnName.MC_MEDIAN_DRAWDOWN_PCT,
            ColumnName.MC_MEDIAN_RETURN_PCT
        ]

        return result

    def get_equity_curve_header_names(self):
        return [
            ColumnName.STRATEGY_ID,
            ColumnName.EXCHANGE,
            ColumnName.CURRENCY_PAIR,
            ColumnName.TIMEFRAME,
            ColumnName.PARAMETERS,
            ColumnName.WFO_CYCLE_TRAINING_ID,
            ColumnName.TESTING_DATE_RANGE,
            ColumnName.EQUITY_CURVE_DATA_POINTS
        ]

    def get_model_data_arr(self):
        result = []
        for row in self._report_rows:
            report_row = row.get_row_data()
            result.append(report_row)
        return result

    def get_equity_curve_report_data_arr(self):
        return [r.equity_curve_report_data.get_report_data() for r in self._report_rows]

    def get_model_df(self):
        df = pd.DataFrame(data=self.get_model_data_arr(), columns=self.get_header_names())
        return df.set_index(self._INDEX_COLUMNS)

    def get_equity_curve_model_df(self):
        df = pd.DataFrame(data=self.get_equity_curve_report_data_arr(), columns=self.get_equity_curve_header_names())
        return df.set_index(self._INDEX_COLUMNS)


class Step3ReportRow(object):
    def __init__(self, run_key, analyzer_data, equity_curve_data, montecarlo_data):
        self.run_key = run_key
        self.analyzer_data = analyzer_data
        self.equity_curve_data = equity_curve_data
        self.montecarlo_data = montecarlo_data
        self.equity_curve_report_data = Step3EquityCurveReportData(run_key, analyzer_data, equity_curve_data.data)

    def get_row_data(self):
        result = [
            self.run_key.strategyid,
            self.run_key.exchange,
            self.run_key.currency_pair,
            self.run_key.timeframe,
            self.run_key.parameters,
            self.run_key.wfo_cycle_training_id,
            self.analyzer_data.wfo_training_period,
            self.analyzer_data.wfo_testing_period,
            self.analyzer_data.trainingdaterange,
            self.analyzer_data.testingdaterange,
            self.analyzer_data.num_wfo_cycles,
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
            self.equity_curve_data.slope,
            self.equity_curve_data.intercept,
            self.equity_curve_data.rvalue,
            self.equity_curve_data.rsquaredvalue,
            self.equity_curve_data.pvalue,
            self.equity_curve_data.stderr,
            self.montecarlo_data.mc_riskofruin_pct,
            self.montecarlo_data.mc_mediandd_pct,
            self.montecarlo_data.mc_medianreturn_pct
        ]
        return result


class Step3EquityCurveReportData(object):
    def __init__(self, run_key, analyzer_data, equitycurvedata):
        self.run_key = run_key
        self.analyzer_data = analyzer_data
        self.equitycurvedata = equitycurvedata

    def get_report_data(self):
        result = [
            self.run_key.strategyid,
            self.run_key.exchange,
            self.run_key.currency_pair,
            self.run_key.timeframe,
            self.run_key.parameters,
            self.run_key.wfo_cycle_training_id,
            self.analyzer_data.testingdaterange,
            self.equitycurvedata
        ]
        return result
