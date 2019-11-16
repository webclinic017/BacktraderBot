from model.backtestmodel import BacktestModel


class Step3Model(object):

    _INDEX_ALL_KEYS_ARR = ["Strategy ID", "Exchange", "Currency Pair", "Timeframe", "Parameters"]

    def __init__(self, step2_df, fromyear, frommonth, toyear, tomonth, columnnameprefix):
        self._step2_df = step2_df
        self._step3_backtest_model = BacktestModel(fromyear, frommonth, toyear, tomonth)
        self._columnnameprefix = columnnameprefix
        self.combined_lr_stats = {}

    def get_backtest_model(self):
        return self._step3_backtest_model

    def get_num_months(self):
        return self._step3_backtest_model.get_num_months()

    def append_prefix(self, arr):
        return ["{}: {}".format(self._columnnameprefix, x) for x in arr]

    def get_header_names(self):
        result = self._step2_df.columns.tolist()
        bktest_header_names = self._step3_backtest_model.get_header_names()
        bktest_header_names = self.strip_unnecessary_fields(bktest_header_names)
        combined_arr = []
        combined_arr.extend(bktest_header_names)
        bktest_header_names = self.append_prefix(combined_arr)
        result.extend(bktest_header_names)
        combined_total_stats_columns = ['Combined Net Profit']
        combined_total_stats_columns = self.append_prefix(combined_total_stats_columns)
        result.extend(combined_total_stats_columns)
        combined_lr_stats_columns = ['Combined Equity Curve Angle', 'Combined Equity Curve Slope', 'Combined Equity Curve Intercept', 'Combined Equity Curve R-value']
        combined_lr_stats_columns = self.append_prefix(combined_lr_stats_columns)
        result.extend(combined_lr_stats_columns)
        return result

    def get_equitycurvedata_model(self):
        return self._step3_backtest_model.get_equitycurvedata_model()

    def strip_unnecessary_fields(self, arr):
        arr = arr[5:]
        return arr

    def get_combined_net_profit(self, step2_net_profit, step3_net_profit):
        return step2_net_profit + step3_net_profit

    def get_combined_total_stats_row(self, step2_row_df, step3_net_profit):
        return [
            self.get_combined_net_profit(step2_row_df["Net Profit"].values[0], step3_net_profit)
        ]

    def get_combined_lr_stats_row(self, combined_lr_stats, row_key):
        stats = combined_lr_stats[row_key]
        return [round(stats.angle), round(stats.slope, 3), round(stats.intercept, 3), round(stats.r_value, 3)]

    def merge_results(self, step2_df, step3_backtest_model):
        final_results = []
        step3_bktest_result_arr = step3_backtest_model.get_model_data_arr()
        step2_df_copy = step2_df.copy()
        step2_df_copy = step2_df_copy.set_index(self._INDEX_ALL_KEYS_ARR)
        for step3_bk_row in step3_bktest_result_arr:
            strategy = step3_bk_row[0]
            exchange = step3_bk_row[1]
            symbol = step3_bk_row[2]
            timeframe = step3_bk_row[3]
            params = step3_bk_row[4]
            step3_net_profit = step3_bk_row[18]
            step3_bk_row = self.strip_unnecessary_fields(step3_bk_row)
            row_key = (strategy, exchange, symbol, timeframe, params)
            step2_row_df = step2_df_copy.loc[[row_key]]
            if len(step2_row_df) > 0:
                result_arr = list(step2_row_df.index.values[0])
                step2_row = list(step2_row_df.values[0])
                result_arr.extend(step2_row)
                result_arr.extend(step3_bk_row)
                result_arr.extend(self.get_combined_total_stats_row(step2_row_df, step3_net_profit))
                result_arr.extend(self.get_combined_lr_stats_row(self.combined_lr_stats, row_key))
                final_results.append(result_arr)
        return final_results

    def get_model_data_arr(self):
        result = self.merge_results(self._step2_df, self._step3_backtest_model)
        return result




