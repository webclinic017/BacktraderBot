
from datetime import date
from calendar import monthrange


class BacktestModel(object):
    def __init__(self, fromyear, frommonth, toyear, tomonth):
        self._monthlystatsprefix = None
        self._report_rows = []
        self._monthly_stats_column_names = self.resolve_monthly_stats_column_names(fromyear, frommonth, toyear, tomonth)
        self._equitycurvedata_model = BacktestEquityCurveDataModel()

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
                if currdate >= fromdate and currdate <= todate:
                    result.append(self.getdaterange_month(year, month, year, month))
        return result

    def add_result_row(self, strategyid, exchange, currency_pair, timeframe, parameters, daterange, startcash, lot_size,
                       total_closed_trades, net_profit, net_profit_pct, avg_monthly_net_profit_pct, max_drawdown_pct,
                       max_drawdown_length, net_profit_to_maxdd, win_rate_pct, num_winning_months, profit_factor, buy_and_hold_return_pct,
                       sqn_number, monthlystatsprefix, monthly_stats, equitycurvedata, equitycurveangle, equitycurveslope,
                       equitycurveintercept, equitycurvervalue, equitycurvepvalue, equitycurvestderr):
        self._monthlystatsprefix = monthlystatsprefix
        row = BacktestReportRow(strategyid, exchange, currency_pair, timeframe, parameters, daterange, startcash, lot_size,
                                total_closed_trades, net_profit, net_profit_pct, avg_monthly_net_profit_pct,
                                max_drawdown_pct, max_drawdown_length, net_profit_to_maxdd, win_rate_pct, num_winning_months,
                                profit_factor, buy_and_hold_return_pct, sqn_number, monthly_stats,
                                equitycurveangle, equitycurveslope, equitycurveintercept, equitycurvervalue, equitycurvepvalue,
                                equitycurvestderr)
        self._report_rows.append(row)
        self._equitycurvedata_model.add_row(strategyid, exchange, currency_pair, timeframe, parameters, daterange,
                                            equitycurvedata)

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
        result = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'Date Range', 'Start Cash', 'Lot Size',
                  'Total Closed Trades', 'Net Profit',
                  'Net Profit, %', 'Avg Monthly Net Profit, %', 'Max Drawdown, %', 'Max Drawdown Length', 'Net Profit To Max Drawdown', 'Win Rate, %',
                  'Winning Months, %', 'Profit Factor', 'Buy & Hold Return, %', 'SQN', 'Equity Curve Angle',
                  'Equity Curve Slope', 'Equity Curve Intercept', 'Equity Curve R-value', 'Equity Curve P-value',
                  'Equity Curve Stderr']

        column_names = self.get_monthly_stats_column_names()
        result.extend(column_names)

        return result

    def sort_results(self):
        arr = self._report_rows.copy()
        self._report_rows = sorted(arr, key=lambda x: (x.net_profit_pct, x.max_drawdown_pct), reverse=True)

    def get_monthly_stats_data(self, entry):
        monthly_netprofit_pct = round(entry.pnl.netprofit.total, 2) if entry else 0
        monthly_won_pct = round(entry.won.total * 100 / entry.total.closed, 2) if entry else 0
        monthly_total_closed = entry.total.closed if entry else 0
        return "{}% | {}% | {}".format(monthly_netprofit_pct, monthly_won_pct, monthly_total_closed)

    def get_monthly_stats_data_arr(self, report_row, column_names):
        result = []
        for column_item in column_names:
            if column_item in report_row.monthly_stats.keys():
                result.append(self.get_monthly_stats_data(report_row.monthly_stats[column_item]))
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

    def get_equitycurvedata_model(self):
        return self._equitycurvedata_model


class BacktestReportRow(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe, parameters, daterange, startcash, lot_size,
                 total_closed_trades, net_profit, net_profit_pct, avg_monthly_net_profit_pct, max_drawdown_pct,
                 max_drawdown_length, net_profit_to_maxdd, win_rate_pct, num_winning_months, profit_factor, buy_and_hold_return_pct,
                 sqn_number, monthly_stats, equitycurveangle, equitycurveslope, equitycurveintercept,
                 equitycurvervalue, equitycurvepvalue, equitycurvestderr):
        self.strategyid = strategyid
        self.exchange = exchange
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.parameters = parameters
        self.daterange = daterange
        self.startcash = startcash
        self.lot_size = lot_size
        self.total_closed_trades = total_closed_trades
        self.net_profit = net_profit
        self.net_profit_pct = net_profit_pct
        self.avg_monthly_net_profit_pct = avg_monthly_net_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_drawdown_length = max_drawdown_length
        self.net_profit_to_maxdd = net_profit_to_maxdd
        self.win_rate_pct = win_rate_pct
        self.num_winning_months = num_winning_months
        self.profit_factor = profit_factor
        self.buy_and_hold_return_pct = buy_and_hold_return_pct
        self.sqn_number = sqn_number
        self.monthly_stats = monthly_stats
        self.equitycurveangle = equitycurveangle
        self.equitycurveslope = equitycurveslope
        self.equitycurveintercept = equitycurveintercept
        self.equitycurvervalue = equitycurvervalue
        self.equitycurvepvalue = equitycurvepvalue
        self.equitycurvestderr = equitycurvestderr

    def get_row_data(self):
        result = [
            self.strategyid,
            self.exchange,
            self.currency_pair,
            self.timeframe,
            self.parameters,
            self.daterange,
            self.startcash,
            self.lot_size,
            self.total_closed_trades,
            self.net_profit,
            self.net_profit_pct,
            self.avg_monthly_net_profit_pct,
            self.max_drawdown_pct,
            self.max_drawdown_length,
            self.net_profit_to_maxdd,
            self.win_rate_pct,
            self.num_winning_months,
            self.profit_factor,
            self.buy_and_hold_return_pct,
            self.sqn_number,
            self.equitycurveangle,
            self.equitycurveslope,
            self.equitycurveintercept,
            self.equitycurvervalue,
            self.equitycurvepvalue,
            self.equitycurvestderr
        ]
        return result


class BacktestEquityCurveDataModel(object):

    _report_rows = []

    def add_row(self, strategyid, exchange, currency_pair, timeframe, parameters, daterange, equitycurvedata):
        row = BacktestEquityCurveDataRow(strategyid, exchange, currency_pair, timeframe, parameters, daterange, equitycurvedata)
        self._report_rows.append(row)

    def get_header_names(self):
        return ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'Date Range', 'Equity Curve Data Points']

    def get_model_data_arr(self):
        result = []
        for row in self._report_rows:
            report_row = row.get_row_data()
            result.append(report_row)
        return result


class BacktestEquityCurveDataRow(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe, parameters, daterange, equitycurvedata):
        self.strategyid = strategyid
        self.exchange = exchange
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.parameters = parameters
        self.daterange = daterange
        self.equitycurvedata = equitycurvedata

    def get_row_data(self):
        result = [
            self.strategyid,
            self.exchange,
            self.currency_pair,
            self.timeframe,
            self.parameters,
            self.daterange,
            self.equitycurvedata
        ]
        return result
