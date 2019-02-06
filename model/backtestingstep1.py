
from datetime import date
from calendar import monthrange

class BacktestingStep1Model(object):

    _monthlystatsprefix = None

    _monthly_stats_column_names = []

    _report_rows = []

    def __init__(self, fromyear, frommonth, toyear, tomonth):
        self.populate_monthly_stats_column_names(fromyear, frommonth, toyear, tomonth)

    def get_month_num_days(self, year, month):
        return monthrange(year, month)[1]

    def getdaterange_month(self, fromyear, frommonth, toyear, tomonth):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(fromyear, frommonth, 1, toyear, tomonth, self.get_month_num_days(toyear, tomonth))

    def populate_monthly_stats_column_names(self, fromyear, frommonth, toyear, tomonth):
        fromdate = date(fromyear, frommonth, 1)
        todate = date(toyear, tomonth, 1)
        for year in range(fromyear, toyear + 1):
            for month in range(1, 13):
                currdate = date(year, month, 1)
                if currdate >= fromdate and currdate <= todate:
                    self._monthly_stats_column_names.append(self.getdaterange_month(year, month, year, month))

    def add_result_row(self, strategyid, exchange, currency_pair, timeframe, parameters, daterange, lot_size, total_closed_trades, net_profit, net_profit_pct, max_drawdown_pct, max_drawdown_length, win_rate_pct, profit_factor, buy_and_hold_return_pct, sqn_number, monthlystatsprefix, monthly_stats):
        self._monthlystatsprefix = monthlystatsprefix
        row = BacktestingStep1ReportRow(strategyid, exchange, currency_pair, timeframe, parameters, daterange, lot_size, total_closed_trades, net_profit, net_profit_pct, max_drawdown_pct, max_drawdown_length, win_rate_pct, profit_factor, buy_and_hold_return_pct, sqn_number, monthly_stats)
        self._report_rows.append(row)

    def get_monthly_stats_column_names(self):
        result = []
        for column_name in self._monthly_stats_column_names:
            result.append("{}: {}".format(self._monthlystatsprefix, column_name))

        return result

    def get_header_names(self):
        result = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'Date Range', 'Lot Size', 'Total Closed Trades', 'Net Profit',
                'Net Profit, %', 'Max Drawdown, %', 'Max Drawdown Length', 'Win Rate, %', 'Profit Factor', 'Buy & Hold Return, %', 'SQN']

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


class BacktestingStep1ReportRow(object):

    strategyid = None

    exchange = None

    currency_pair = None

    timeframe = None

    parameters = None

    daterange = None

    lot_size = None

    total_closed_trades = None

    net_profit = None

    net_profit_pct = None

    max_drawdown_pct = None

    max_drawdown_length = None

    win_rate_pct = None

    profit_factor = None

    buy_and_hold_return_pct = None

    sqn_number = None

    monthly_stats = None

    def __init__(self, strategyid, exchange, currency_pair, timeframe, parameters, daterange, lot_size, total_closed_trades, net_profit, net_profit_pct, max_drawdown_pct, max_drawdown_length, win_rate_pct, profit_factor, buy_and_hold_return_pct, sqn_number, monthly_stats):
        self.strategyid = strategyid
        self.exchange = exchange
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.parameters = parameters
        self.daterange = daterange
        self.lot_size = lot_size
        self.total_closed_trades = total_closed_trades
        self.net_profit = net_profit
        self.net_profit_pct = net_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_drawdown_length = max_drawdown_length
        self.win_rate_pct = win_rate_pct
        self.profit_factor = profit_factor
        self.buy_and_hold_return_pct = buy_and_hold_return_pct
        self.sqn_number = sqn_number
        self.monthly_stats = monthly_stats

    def get_row_data(self):
        result = [
                self.strategyid,
                self.exchange,
                self.currency_pair,
                self.timeframe,
                self.parameters,
                self.daterange,
                self.lot_size,
                self.total_closed_trades,
                self.net_profit,
                self.net_profit_pct,
                self.max_drawdown_pct,
                self.max_drawdown_length,
                self.win_rate_pct,
                self.profit_factor,
                self.buy_and_hold_return_pct,
                self.sqn_number]

        return result
