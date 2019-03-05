import itertools


class Step5Model(object):

    EMPTY_VALUE = "---------------------------------------------"

    def __init__(self):
        self._result_columns = []
        self._dateranges_arr = []

    def get_pct_val(self, val):
        return "{}%".format(val)

    def calc_sum(self, arr):
        return sum(arr)

    def calc_average(self, arr):
        len_non_zero = len(list(filter(lambda x: (x != 0), arr)))
        return sum(arr) / float(len_non_zero) if len_non_zero != 0 else 0

    def calc_worst(self, arr):
        count_negative_numbers = sum(1 for n in arr if n < 0)
        if count_negative_numbers == 0:
            return min(n for n in arr if n != 0)
        else:
            return min(arr)

    def calc_negative_elements_num(self, arr):
        return len(list(filter(lambda x: (x < 0), arr)))

    def add_result_column(self, strategyid, exchange, currency_pair, timeframe, parameters, startcash, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats):
        self._dateranges_arr = monthly_stats.keys()
        simple_sum_net_profit_pct_monthly = round(self.calc_sum(monthly_stats.values()), 2)
        average_net_profit_pct_monthly = round(self.calc_average(monthly_stats.values()), 2)
        worst_net_profit_pct_monthly = round(self.calc_worst(monthly_stats.values()), 2)
        num_months_in_loss = self.calc_negative_elements_num(monthly_stats.values())
        entry = Step5Column(strategyid, exchange, currency_pair, timeframe, parameters, startcash, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats,
                            simple_sum_net_profit_pct_monthly, average_net_profit_pct_monthly, worst_net_profit_pct_monthly, num_months_in_loss)
        self._result_columns.append(entry)

    def get_vert_header_column(self):
        result = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'Commission', 'Leverage', 'Pyramiding', 'Profit Factor', 'Win Rate, %', 'Max Drawdown, %', 'Combined Total Closed Trades']
        result.append(Step5Model.EMPTY_VALUE)
        result.extend(self._dateranges_arr)
        result.append(Step5Model.EMPTY_VALUE)
        result.extend(['Simple Sum Net Profit, %', 'Avg Monthly Net Profit, %', 'Worst Monthly Net Profit, %', 'Losing Months'])
        return result

    def get_vert_avg_footer_column(self):
        result = ['', '', '', '', '', '', '', 'Portfolio Strategy Average Net Profit, %', '', '', '', '']
        result.append(Step5Model.EMPTY_VALUE)

        for daterange_val in self._dateranges_arr:
            monthly_net_profict_pct_list = [x.monthly_stats[daterange_val] for x in self._result_columns]
            result.append(self.get_pct_val(round(self.calc_average(monthly_net_profict_pct_list), 2)))

        result.append(Step5Model.EMPTY_VALUE)

        result.extend(["", "", "", ""])

        return result

    def get_vert_sum_footer_column(self):
        result = ['', '', '', '', '', '', '', 'Portfolio Monthly Net Profit, %', '', '', '', '']
        result.append(Step5Model.EMPTY_VALUE)

        monthly_equity_change_pct_list = []
        accum_equity_list = [x.startcash for x in self._result_columns]
        for daterange_val in self._dateranges_arr:
            counter = itertools.count()
            prev_month_accum_equity = sum(accum_equity_list)
            for column in self._result_columns:
                idx = next(counter)
                monthly_netprofit_pct = column.monthly_stats[daterange_val]
                accum_equity_list[idx] = accum_equity_list[idx] * (1 + monthly_netprofit_pct/100)
            curr_month_accum_equity = sum(accum_equity_list)
            monthly_equity_change_pct = round((curr_month_accum_equity - prev_month_accum_equity) * 100 / prev_month_accum_equity, 2)
            monthly_equity_change_pct_list.append(monthly_equity_change_pct)
            result.append(self.get_pct_val(monthly_equity_change_pct))

        result.append(Step5Model.EMPTY_VALUE)

        result.append(self.get_pct_val(round(self.calc_sum(monthly_equity_change_pct_list), 2)))
        result.append(self.get_pct_val(round(self.calc_average(monthly_equity_change_pct_list), 2)))
        result.append(self.get_pct_val(round(self.calc_worst(monthly_equity_change_pct_list), 2)))
        result.append(self.calc_negative_elements_num(monthly_equity_change_pct_list))

        return result

    def get_vert_worst_month_footer_column(self):
        result = ['', '', '', '', '', '', '', 'Portfolio Worst Strategy Net Profit, %', '', '', '', '']
        result.append(Step5Model.EMPTY_VALUE)

        for daterange_val in self._dateranges_arr:
            monthly_net_profict_pct_list = [x.monthly_stats[daterange_val] for x in self._result_columns]
            result.append(self.get_pct_val(round(self.calc_worst(monthly_net_profict_pct_list), 2)))

        result.append(Step5Model.EMPTY_VALUE)

        result.extend(["", "", "", ""])

        return result

    def get_vert_losing_months_footer_column(self):
        result = ['', '', '', '', '', '', '', 'Portfolio Losing Strategies Per Month, %', '', '', '', '']
        result.append(Step5Model.EMPTY_VALUE)

        for daterange_val in self._dateranges_arr:
            monthly_net_profict_pct_list = [x.monthly_stats[daterange_val] for x in self._result_columns]
            val = round(self.calc_negative_elements_num(monthly_net_profict_pct_list) * 100 / len(monthly_net_profict_pct_list), 2)
            val_str = self.get_pct_val(val)
            result.append(val_str)

        result.append(Step5Model.EMPTY_VALUE)
        result.extend(["", "", "", ""])
        return result

    def get_model_data_arr(self):
        result_matrix = []
        result_matrix.append(self.get_vert_header_column())
        for column in self._result_columns:
            result_matrix.append(column.get_data())
        result_matrix.append(self.get_vert_sum_footer_column())
        result_matrix.append(self.get_vert_avg_footer_column())
        result_matrix.append(self.get_vert_worst_month_footer_column())
        result_matrix.append(self.get_vert_losing_months_footer_column())

        # Transpose matrix
        result = [*zip(*result_matrix)]
        return result


class Step5Column(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe, parameters, startcash, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats,
                 simple_sum_net_profit_pct_monthly, average_net_profit_pct_monthly, worst_net_profit_pct_monthly, num_months_in_loss):
        self.strategyid = strategyid
        self.exchange = exchange
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.parameters = parameters
        self.startcash = startcash
        self.commission = commission
        self.leverage = leverage
        self.pyramiding = pyramiding
        self.profit_factor = profit_factor
        self.win_rate_pct = win_rate_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.total_closed_trades = total_closed_trades
        self.monthly_stats = monthly_stats
        self.simple_sum_net_profit_pct_monthly = simple_sum_net_profit_pct_monthly
        self.average_net_profit_pct_monthly = average_net_profit_pct_monthly
        self.worst_net_profit_pct_monthly = worst_net_profit_pct_monthly
        self.num_months_in_loss = num_months_in_loss

    def get_pct_val(self, val):
        return "{}%".format(val)

    def get_data(self):
        result = [
            self.strategyid,
            self.exchange,
            self.currency_pair,
            self.timeframe,
            self.parameters,
            self.commission,
            self.leverage,
            self.pyramiding,
            self.profit_factor,
            self.win_rate_pct,
            self.max_drawdown_pct,
            self.total_closed_trades]
        result.append(Step5Model.EMPTY_VALUE)
        result.extend([self.get_pct_val(x) for x in self.monthly_stats.values()])
        result.append(Step5Model.EMPTY_VALUE)
        result.extend([
            self.get_pct_val(self.simple_sum_net_profit_pct_monthly),
            self.get_pct_val(self.average_net_profit_pct_monthly),
            self.get_pct_val(self.worst_net_profit_pct_monthly),
            self.num_months_in_loss
        ])
        return result
