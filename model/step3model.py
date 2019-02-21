from model.backtestmodel import BacktestModel


class Step3Model(object):

    _INDEX_ALL_KEYS_ARR = ["Strategy ID", "Exchange", "Currency Pair", "Timeframe", "Parameters"]

    _step2_df = None
    _step3_backtest_model = None
    _columnnameprefix = None

    def __init__(self, step2_df, fromyear, frommonth, toyear, tomonth, columnnameprefix):
        self._step2_df = step2_df
        self._step3_backtest_model = BacktestModel(fromyear, frommonth, toyear, tomonth)
        self._columnnameprefix = columnnameprefix

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
        return result

    def get_equitycurvedata_model(self):
        return self._step3_backtest_model.get_equitycurvedata_model()

    def strip_unnecessary_fields(self, arr):
        arr = arr[5:]
        return arr

    def merge_results(self, step2_df, backtest_model):
        final_results = []
        bktest_result_arr = backtest_model.get_model_data_arr()
        step2_df_copy = step2_df.copy()
        step2_df_copy = step2_df_copy.set_index(self._INDEX_ALL_KEYS_ARR)
        for bk_row in bktest_result_arr:
            strategy = bk_row[0]
            exchange = bk_row[1]
            symbol = bk_row[2]
            timeframe = bk_row[3]
            params = bk_row[4]
            bk_row = self.strip_unnecessary_fields(bk_row)
            found_row_df = step2_df_copy.loc[[(strategy, exchange, symbol, timeframe, params)]]
            if len(found_row_df) > 0:
                result_arr = list(found_row_df.index.values[0])
                found_row = list(found_row_df.values[0])
                result_arr.extend(found_row)
                result_arr.extend(bk_row)
                final_results.append(result_arr)
        return final_results

    def get_model_data_arr(self):
        result = self.merge_results(self._step2_df, self._step3_backtest_model)
        return result




