
from datetime import date
from calendar import monthrange


class BacktestModel(object):
    def __init__(self, fromyear, frommonth, toyear, tomonth):
        self._monthlystatsprefix = None
        self._report_rows = []
        self._monthly_stats_column_names = self.resolve_monthly_stats_column_names(fromyear, frommonth, toyear, tomonth)
        self._equity_curve_report_rows = []

    def get_month_num_days(self, year, month):
        return monthrange(year, month)[1]

    def getdaterange_month(self, fromyear, frommonth, toyear, tomonth):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(fromyear, frommonth, 1, toyear, tomonth, self.get_month_num_days(toyear, tomonth))

    def resolve_monthly_stats_column_names(self, fromyear, frommonth, toyear, tomonth):
        result = []
        fromdate = date(fromyear, frommonth, 1)
        todate = date(toyear, tomonth, 1)
        for year in range(fromyear, toyear + 1):
            for month in range(1, 13):
                currdate = date(year, month, 1)
                if fromdate <= currdate <= todate:
                    result.append(self.getdaterange_month(year, month, year, month))
        return result

    def add_result_row(self, run_key, analyzer_data, equity_curve_data, montecarlo_data):
        self._monthlystatsprefix = analyzer_data.monthlystatsprefix
        row = BacktestReportRow(run_key, analyzer_data, equity_curve_data, montecarlo_data)
        self._report_rows.append(row)

    def get_monthly_stats_column_names(self):
        result = []

        if self._monthlystatsprefix is None or self._monthlystatsprefix == "":
            return self._monthly_stats_column_names

        for column_name in self._monthly_stats_column_names:
            result.append("{}: {}".format(self._monthlystatsprefix, column_name))

        return result

    def get_num_months(self):
        return len(self._monthly_stats_column_names)

    def get_header_names(self):
        result = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'WFO Cycle', 'Date Range', 'Start Cash', 'Lot Size',
                  'Processing Status', 'Total Closed Trades', 'Trades # SL Count', 'Trades # TSL Count', 'TSL Moved Count', 'Trades # TP Count', 'Trades # TTP Count', 'TTP Moved Count',
                  'Trades # TB Count', 'TB Moved Count', 'Trades # DCA Triggered Count', 'Net Profit', 'Net Profit, %', 'Avg Monthly Net Profit, %', 'Max Drawdown, %', 'Max Drawdown Length',
                  'Net Profit To Max Drawdown', 'Win Rate, %', 'Avg # Bars In Trades', 'Bars In Trades Ratio, %',
                  'Winning Months, %', 'Profit Factor', 'Buy & Hold Return, %', 'SQN', 'Equity Curve Angle',
                  'Equity Curve Slope', 'Equity Curve Intercept', 'Equity Curve R-value', 'Equity Curve R-Squared value', 'Equity Curve P-value', 'Equity Curve Stderr',
                  'MC: Risk Of Ruin, %',  'MC: Median Drawdown, %', 'MC: Median Return, %']

        column_names = self.get_monthly_stats_column_names()
        result.extend(column_names)

        return result

    def get_equity_curve_header_names(self):
        return ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'WFO Cycle', 'Date Range', 'Equity Curve Data Points']

    def filter_top_results(self, number_top_rows):
        self._report_rows = sorted(self._report_rows, key=lambda x: (x.run_key.wfo_cycle, x.analyzer_data.net_profit_to_maxdd), reverse=True)
        self._report_rows = self._report_rows[:number_top_rows]

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


class BacktestReportRow(object):
    def __init__(self, run_key, analyzer_data, equity_curve_data, montecarlo_data):
        self.run_key = run_key
        self.analyzer_data = analyzer_data
        self.equity_curve_data = equity_curve_data
        self.montecarlo_data = montecarlo_data
        self.equity_curve_report_data = BacktestEquityCurveReportData(run_key, analyzer_data.daterange, equity_curve_data.equitycurvedata)

    def get_row_data(self):
        result = [
            self.run_key.strategyid,
            self.run_key.exchange,
            self.run_key.currency_pair,
            self.run_key.timeframe,
            self.run_key.parameters,
            self.run_key.wfo_cycle,
            self.analyzer_data.daterange,
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
            self.equity_curve_data.equitycurveangle,
            self.equity_curve_data.equitycurveslope,
            self.equity_curve_data.equitycurveintercept,
            self.equity_curve_data.equitycurvervalue,
            self.equity_curve_data.equitycurversquaredvalue,
            self.equity_curve_data.equitycurvepvalue,
            self.equity_curve_data.equitycurvestderr,
            self.montecarlo_data.mc_riskofruin_pct,
            self.montecarlo_data.mc_mediandd_pct,
            self.montecarlo_data.mc_medianreturn_pct
        ]
        return result


class BacktestEquityCurveReportData(object):
    def __init__(self, run_key, daterange, equitycurvedata):
        self.run_key = run_key
        self.daterange = daterange
        self.equitycurvedata = equitycurvedata

    def get_report_data(self):
        result = [
            self.run_key.strategyid,
            self.run_key.exchange,
            self.run_key.currency_pair,
            self.run_key.timeframe,
            self.run_key.parameters,
            self.run_key.wfo_cycle,
            self.daterange,
            self.equitycurvedata
        ]
        return result
