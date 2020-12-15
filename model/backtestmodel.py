
from datetime import date
from calendar import monthrange
from model.reports_common import ColumnName
from model.common import WFOMode
import pandas as pd


class BacktestModel(object):

    _INDEX_COLUMNS = [ColumnName.STRATEGY_ID, ColumnName.EXCHANGE, ColumnName.CURRENCY_PAIR, ColumnName.TIMEFRAME]

    def __init__(self, wfo_mode, wfo_cycles):
        self._wfo_mode = wfo_mode
        self._report_rows = []
        self._wfo_cycles = wfo_cycles
        self._monthly_stats_column_names = self.resolve_monthly_stats_column_names(wfo_mode, wfo_cycles)
        self._equity_curve_report_rows = []

    def get_month_num_days(self, year, month):
        return monthrange(year, month)[1]

    def getdaterange_month(self, fromyear, frommonth, toyear, tomonth):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(fromyear, frommonth, 1, toyear, tomonth, self.get_month_num_days(toyear, tomonth))

    def resolve_monthly_stats_column_names(self, wfo_mode, wfo_cycles):
        result = []
        first_wfo_cycle = wfo_cycles[0]
        last_wfo_cycle = wfo_cycles[-1]
        if wfo_mode == WFOMode.WFO_MODE_TRAINING:
            fromyear  = first_wfo_cycle.training_start_date.date().year
            frommonth = first_wfo_cycle.training_start_date.date().month
            toyear    = last_wfo_cycle.training_end_date.date().year
            tomonth   = last_wfo_cycle.training_end_date.date().month
        else:
            fromyear  = first_wfo_cycle.testing_start_date.date().year
            frommonth = first_wfo_cycle.testing_start_date.date().month
            toyear    = last_wfo_cycle.testing_end_date.date().year
            tomonth   = last_wfo_cycle.testing_end_date.date().month

        fromdate = date(fromyear, frommonth, 1)
        todate = date(toyear, tomonth, 1)
        for year in range(fromyear, toyear + 1):
            for month in range(1, 13):
                currdate = date(year, month, 1)
                if fromdate <= currdate <= todate:
                    result.append(self.getdaterange_month(year, month, year, month))
        return result

    def add_result_row(self, run_key, analyzer_data, equity_curve_data, montecarlo_data):
        row = BacktestReportRow(run_key, analyzer_data, equity_curve_data, montecarlo_data)
        self._report_rows.append(row)

    def get_monthly_stats_column_names(self):
        return self._monthly_stats_column_names

    def get_num_months(self):
        return len(self._monthly_stats_column_names)

    def get_header_names(self):
        result = [
            ColumnName.STRATEGY_ID,
            ColumnName.EXCHANGE,
            ColumnName.CURRENCY_PAIR,
            ColumnName.TIMEFRAME,
            ColumnName.PARAMETERS,
            ColumnName.WFO_CYCLE_ID,
            ColumnName.WFO_CYCLE_TRAINING_ID,
            ColumnName.WFO_TRAINING_PERIOD,
            ColumnName.WFO_TESTING_PERIOD,
            ColumnName.TRAINING_DATE_RANGE,
            ColumnName.TESTING_DATE_RANGE,
            ColumnName.NUM_WFO_CYCLES,
            ColumnName.START_CASH,
            ColumnName.LOT_SIZE,
            ColumnName.PROCESSING_STATUS,
            ColumnName.TOTAL_CLOSED_TRADES,
            ColumnName.TRADES_NUM_SL_COUNT,
            ColumnName.TRADES_NUM_TSL_COUNT,
            ColumnName.TSL_MOVED_COUNT,
            ColumnName.TRADES_NUM_TP_COUNT,
            ColumnName.TRADES_NUM_TTP_COUNT,
            ColumnName.TTP_MOVED_COUNT,
            ColumnName.TRADES_NUM_TB_COUNT,
            ColumnName.TB_MOVED_COUNT,
            ColumnName.TRADES_NUM_DCA_TRIGGERED_COUNT,
            ColumnName.NET_PROFIT,
            ColumnName.NET_PROFIT_PCT,
            ColumnName.AVG_MONTHLY_NET_PROFIT_PCT,
            ColumnName.MAX_DRAWDOWN_PCT,
            ColumnName.MAX_DRAWDOWN_LENGTH,
            ColumnName.NET_PROFIT_TO_MAX_DRAWDOWN,
            ColumnName.WIN_RATE_PCT,
            ColumnName.AVG_NUM_BARS_IN_TRADES,
            ColumnName.BARS_IN_TRADES_RATIO_PCT,
            ColumnName.WINNING_MONTHS_PCT,
            ColumnName.PROFIT_FACTOR,
            ColumnName.BUY_AND_HOLD_RETURN_PCT,
            ColumnName.SQN,
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

        column_names = self.get_monthly_stats_column_names()
        result.extend(column_names)

        return result

    def get_equity_curve_header_names(self):
        return [
            ColumnName.STRATEGY_ID,
            ColumnName.EXCHANGE,
            ColumnName.CURRENCY_PAIR,
            ColumnName.TIMEFRAME,
            ColumnName.PARAMETERS,
            ColumnName.WFO_CYCLE_ID,
            ColumnName.WFO_CYCLE_TRAINING_ID,
            ColumnName.TRAINING_DATE_RANGE,
            ColumnName.TESTING_DATE_RANGE,
            ColumnName.NUM_WFO_CYCLES,
            ColumnName.EQUITY_CURVE_DATA_POINTS
        ]

    def filter_wfo_training_top_results(self, number_top_rows):
        self._report_rows = sorted(self._report_rows, key=lambda x: (x.run_key.wfo_cycle_id, x.analyzer_data.net_profit_to_maxdd,  x.equity_curve_data.rvalue), reverse=True)
        self._report_rows = self._report_rows[:number_top_rows]

        counter = 1
        for report_row in self._report_rows:
            report_row.run_key.wfo_cycle_training_id = counter
            counter = counter + 1

    def sort_wfo_testing_results(self):
        self._report_rows = sorted(self._report_rows, key=lambda x: (x.run_key.strategyid, x.run_key.exchange, x.run_key.currency_pair, x.run_key.timeframe, x.run_key.wfo_cycle_training_id, x.run_key.wfo_cycle_id), reverse=False)

    def get_monthly_stats_data(self, entry):
        monthly_netprofit = round(entry.pnl.netprofit.total) if entry else 0
        monthly_netprofit_pct = round(entry.pnl.netprofit.pct, 2) if entry else 0
        monthly_won_pct = round(entry.won.total * 100 / entry.total.closed, 2) if entry else 0
        monthly_total_closed = entry.total.closed if entry else 0
        return "{} | {}% | {}% | {}".format(monthly_netprofit, monthly_netprofit_pct, monthly_won_pct, monthly_total_closed)

    def get_monthly_stats_data_arr(self, report_row, column_names):
        result = []
        monthly_stats_dict = report_row.analyzer_data.monthly_stats
        for column_item in column_names:
            if column_item in monthly_stats_dict.keys():
                result.append(self.get_monthly_stats_data(monthly_stats_dict[column_item]))
            else:
                result.append(self.get_monthly_stats_data(None))
        return result

    def get_model_data_arr(self):
        result = []
        column_names = self._monthly_stats_column_names
        for row in self._report_rows:
            report_row = row.get_row_data()
            monthly_stats_data = self.get_monthly_stats_data_arr(row, column_names)
            report_row.extend(monthly_stats_data)
            result.append(report_row)
        return result

    def get_equity_curve_report_data_arr(self):
        return [r.equity_curve_report_data.get_report_data() for r in self._report_rows]

    def get_report_row_by_wfo_cycle(self, wfo_cycle_id, wfo_cycle_training_id):
        for row in self._report_rows:
            if row.run_key.wfo_cycle_id == wfo_cycle_id and row.run_key.wfo_cycle_training_id == wfo_cycle_training_id:
                return row
        return None

    def get_model_df(self):
        df = pd.DataFrame(data=self.get_model_data_arr(), columns=self.get_header_names())
        return df.set_index(self._INDEX_COLUMNS)

    def get_equity_curve_model_df(self):
        df = pd.DataFrame(data=self.get_equity_curve_report_data_arr(), columns=self.get_equity_curve_header_names())
        return df.set_index(self._INDEX_COLUMNS)


class BacktestReportRow(object):
    def __init__(self, run_key, analyzer_data, equity_curve_data, montecarlo_data):
        self.run_key = run_key
        self.analyzer_data = analyzer_data
        self.equity_curve_data = equity_curve_data
        self.montecarlo_data = montecarlo_data
        self.equity_curve_report_data = BacktestEquityCurveReportData(run_key, analyzer_data, equity_curve_data.data)

    def get_row_data(self):
        result = [
            self.run_key.strategyid,
            self.run_key.exchange,
            self.run_key.currency_pair,
            self.run_key.timeframe,
            self.run_key.parameters,
            self.run_key.wfo_cycle_id,
            self.run_key.wfo_cycle_training_id,
            self.analyzer_data.wfo_training_period,
            self.analyzer_data.wfo_testing_period,
            self.analyzer_data.trainingdaterange,
            self.analyzer_data.testingdaterange,
            self.analyzer_data.num_wfo_cycles,
            self.analyzer_data.startcash,
            self.analyzer_data.lot_size,
            self.analyzer_data.processing_status,
            self.analyzer_data.total_closed_trades,
            self.analyzer_data.sl_trades_count,
            self.analyzer_data.tsl_trades_count,
            self.analyzer_data.tsl_moved_count,
            self.analyzer_data.tp_trades_count,
            self.analyzer_data.ttp_trades_count,
            self.analyzer_data.ttp_moved_count,
            self.analyzer_data.tb_trades_count,
            self.analyzer_data.tb_moved_count,
            self.analyzer_data.dca_triggered_count,
            self.analyzer_data.net_profit,
            self.analyzer_data.net_profit_pct,
            self.analyzer_data.avg_monthly_net_profit_pct,
            self.analyzer_data.max_drawdown_pct,
            self.analyzer_data.max_drawdown_length,
            self.analyzer_data.net_profit_to_maxdd,
            self.analyzer_data.win_rate_pct,
            self.analyzer_data.trades_len_avg,
            self.analyzer_data.trade_bars_ratio_pct,
            self.analyzer_data.num_winning_months,
            self.analyzer_data.profit_factor,
            self.analyzer_data.buy_and_hold_return_pct,
            self.analyzer_data.sqn_number,
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


class BacktestEquityCurveReportData(object):
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
            self.run_key.wfo_cycle_id,
            self.run_key.wfo_cycle_training_id,
            self.analyzer_data.trainingdaterange,
            self.analyzer_data.testingdaterange,
            self.analyzer_data.num_wfo_cycles,
            self.equitycurvedata
        ]
        return result
