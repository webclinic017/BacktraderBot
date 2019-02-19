import ast
from model.backtestmodel import BacktestModel


class Step3Model(object):

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
        combined_arr = ["Start Cash"]
        combined_arr.extend(bktest_header_names)
        bktest_header_names = self.append_prefix(combined_arr)
        result.extend(bktest_header_names)
        return result

    def get_equitycurvedata_model(self):
        return self._step3_backtest_model.get_equitycurvedata_model()

    def get_parameters_map(self, parameters_json):
        return ast.literal_eval(parameters_json)

    def strip_params_to_compare(self, params_json):
        pmap = self.get_parameters_map(params_json)
        del pmap["startcash"]
        del pmap["fromyear"]
        del pmap["frommonth"]
        del pmap["fromday"]
        del pmap["toyear"]
        del pmap["tomonth"]
        del pmap["today"]
        return pmap

    def compare_params(self, params1_json, params2_json):
        pmap1 = self.strip_params_to_compare(params1_json)
        pmap2 = self.strip_params_to_compare(params2_json)
        return pmap1 == pmap2

    def find_matching_row(self, src_arr, row):
        result = []
        strategy_id = row[0]
        exchange = row[1]
        symbol = row[2]
        timeframe = row[3]
        params = row[4]
        for src_row in src_arr:
            src_strategy_id = src_row[0]
            src_exchange = src_row[1]
            src_symbol = src_row[2]
            src_timeframe = src_row[3]
            src_params = src_row[4]
            if src_strategy_id == strategy_id and src_exchange == exchange and src_symbol == symbol and src_timeframe == timeframe and self.compare_params(src_params, params):
                result = src_row
                break

        return list(result)

    def strip_unnecessary_fields(self, arr):
        arr = arr[5:]
        return arr

    def get_startcash_from_params(self, params_json):
        pmap = self.get_parameters_map(params_json)
        return pmap["startcash"]

    def merge_results(self, step2_df, backtest_model):
        final_results = []
        step2_df = step2_df.reset_index(drop=True)
        input_arr = step2_df.values
        bktest_result_arr = backtest_model.get_model_data_arr()

        for bk_row in bktest_result_arr:
            found_row = self.find_matching_row(input_arr, bk_row)
            if len(found_row) > 0:
                params_bktest = bk_row[4]
                bk_row = self.strip_unnecessary_fields(bk_row)
                startcash = self.get_startcash_from_params(params_bktest)
                found_row.append(startcash)
                found_row.extend(bk_row)
                final_results.append(found_row)
        return final_results

    def get_model_data_arr(self):
        result = self.merge_results(self._step2_df, self._step3_backtest_model)
        return result




