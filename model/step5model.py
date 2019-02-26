
class Step5Model(object):

    EMPTY_VALUE = "---------------------------------------------"

    def __init__(self):
        self._result_columns = []
        self._dateranges_arr = []

    def calc_simple_sum(self, arr):
        return sum(arr)

    def calc_average(self, arr):
        len_non_zero = len(list(filter(lambda x: (x != 0), arr)))
        return sum(arr) / float(len_non_zero)

    def calc_worst_value(self, arr):
        return min(arr)

    def calc_negative_elements_num(self, arr):
        return len(list(filter(lambda x: (x < 0), arr)))

    def add_result_column(self, strategyid, exchange, currency_pair, timeframe, parameters, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats):
        self._dateranges_arr = monthly_stats.keys()
        simple_sum_net_profit_pct_monthly = round(self.calc_simple_sum(monthly_stats.values()), 2)
        average_net_profit_pct_monthly = round(self.calc_average(monthly_stats.values()), 2)
        worst_net_profit_pct_monthly = round(self.calc_worst_value(monthly_stats.values()), 2)
        num_months_in_loss = self.calc_negative_elements_num(monthly_stats.values())
        entry = Step5Column(strategyid, exchange, currency_pair, timeframe, parameters, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats,
                            simple_sum_net_profit_pct_monthly, average_net_profit_pct_monthly, worst_net_profit_pct_monthly, num_months_in_loss)
        self._result_columns.append(entry)

    def get_vert_header_column(self):
        result = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters', 'Commission', 'Leverage', 'Pyramiding', 'Profit Factor', 'Win Rate, %', 'Max Drawdown, %', 'Total Closed Trades']
        result.append(Step5Model.EMPTY_VALUE)
        result.extend(self._dateranges_arr)
        result.append(Step5Model.EMPTY_VALUE)
        result.extend(['Simple Sum Net Profit, %', 'Avg Monthly Net Profit, %', 'Worst Monthly Net Profit, %', 'Losing Months'])
        return result

    def get_vert_footer_column(self):
        result = ['', '', '', '', '', '', '', 'Average']
        profit_factor_list = [x.profit_factor for x in self._result_columns]
        win_rate_pct_list = [x.win_rate_pct for x in self._result_columns]
        max_drawdown_pct_list = [x.max_drawdown_pct for x in self._result_columns]
        total_closed_trades_list = [x.total_closed_trades for x in self._result_columns]
        result.append(round(self.calc_average(profit_factor_list), 2))
        result.append(round(self.calc_average(win_rate_pct_list), 2))
        result.append(round(self.calc_average(max_drawdown_pct_list), 2))
        result.append(int(self.calc_average(total_closed_trades_list)))
        result.append(Step5Model.EMPTY_VALUE)

        for daterange_val in self._dateranges_arr:
            monthly_net_profict_pct_list = [x.monthly_stats[daterange_val] for x in self._result_columns]
            result.append(round(self.calc_average(monthly_net_profict_pct_list), 2))

        result.append(Step5Model.EMPTY_VALUE)

        simple_sum_net_profit_pct_monthly_list = [x.simple_sum_net_profit_pct_monthly for x in self._result_columns]
        average_net_profit_pct_monthly_list = [x.average_net_profit_pct_monthly for x in self._result_columns]
        worst_net_profit_pct_monthly_list = [x.worst_net_profit_pct_monthly for x in self._result_columns]
        num_months_in_loss_list = [x.num_months_in_loss for x in self._result_columns]
        result.append(round(self.calc_average(simple_sum_net_profit_pct_monthly_list), 2))
        result.append(round(self.calc_average(average_net_profit_pct_monthly_list), 2))
        result.append(round(self.calc_average(worst_net_profit_pct_monthly_list), 2))
        result.append(round(self.calc_average(num_months_in_loss_list), 2))

        return result

    def get_model_data_arr(self):
        result_matrix = []
        result_matrix.append(self.get_vert_header_column())
        for column in self._result_columns:
            result_matrix.append(column.get_data())
        result_matrix.append(self.get_vert_footer_column())

        # Transpose matrix
        result = [*zip(*result_matrix)]
        return result


class Step5Column(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe, parameters, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats,
                 simple_sum_net_profit_pct_monthly, average_net_profit_pct_monthly, worst_net_profit_pct_monthly, num_months_in_loss):
        self.strategyid = strategyid
        self.exchange = exchange
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.parameters = parameters
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
        result.extend(self.monthly_stats.values())
        result.append(Step5Model.EMPTY_VALUE)
        result.extend([
            self.simple_sum_net_profit_pct_monthly,
            self.average_net_profit_pct_monthly,
            self.worst_net_profit_pct_monthly,
            self.num_months_in_loss
        ])
        return result
