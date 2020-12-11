from .common import BacktestRunKey
from .common import BacktestAnalyzerData
from .common import EquityCurveData
from .common import MonteCarloData
from montecarlo.montecarlo import MonteCarloSimulator
from model.reports_common import ColumnName
from backtrader.utils import AutoOrderedDict
from model.linreg import LinearRegressionCalculator
import json
import ast
import pandas as pd
import numpy as np


class DrawDownCalculator(object):
    def __init__(self, startcash):
        self.rets = AutoOrderedDict()

        self.rets.len = 0
        self.rets.drawdown = 0.0
        self.rets.moneydown = 0.0

        self.rets.max.len = 0.0
        self.rets.max.drawdown = 0.0
        self.rets.max.moneydown = 0.0

        self.startcash = startcash
        self.maxportfoliovalue = startcash

    def calculate(self, equity_curve_data_dict):
        for date, equity in equity_curve_data_dict.items():
            r = self.rets
            tradeclosevalue = self.startcash + equity
            if tradeclosevalue < self.maxportfoliovalue:
                r.moneydown = moneydown = tradeclosevalue - self.maxportfoliovalue
                r.drawdown = drawdown = 100.0 * moneydown / self.maxportfoliovalue
                r.len = r.len + 1 if drawdown else 0
            else:
                self.maxportfoliovalue = tradeclosevalue
                r.moneydown = moneydown = 0
                r.drawdown = drawdown = 0
                r.len = 0

            # maximum drawdown values
            r.max.moneydown = min(r.max.moneydown, moneydown)
            r.max.drawdown = min(r.max.drawdown, drawdown)
            r.max.len = max(r.max.len, r.len)
        return self.rets


class Step3ModelGenerator(object):

    def __init__(self):
        pass

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def merge_wfo_testing_params(self, data_df):
        result = ""
        for index, row in data_df.iterrows():
            params_json = row[ColumnName.PARAMETERS]
            date = row[ColumnName.TESTING_DATE_RANGE]
            params_str = "{}:{}".format(date, params_json)
            result += "{}\n".format(params_str)
        return result

    def get_pct_fmt(self, val):
        return "{}%".format(round(val, 2))

    def get_df_column_val(self, df, row_num, column_name):
        return df.iloc[row_num][column_name]

    def get_sum_values_val(self, df, column_name):
        return df[column_name].sum()

    def get_equity_curve_data_points(self, series):
        equity_curve_data_points_str = series[ColumnName.EQUITY_CURVE_DATA_POINTS]
        return json.loads(equity_curve_data_points_str)

    def concat_equity_curve_data_rows(self, df):
        result_dict = dict()
        for index, row in df.iterrows():
            equity_curve_dict = self.get_equity_curve_data_points(row)
            result_dict.update(equity_curve_dict)
        return result_dict

    def get_equitycurve_data(self, equity_curve_data_dict):
        return json.dumps(equity_curve_data_dict)

    def calculate_winrate_pct(self, df):
        total_closed_counter = 0
        total_won_counter = 0
        for index, row in df.iterrows():
            total_closed = row[ColumnName.TOTAL_CLOSED_TRADES]
            wr = row[ColumnName.WIN_RATE_PCT]
            wr = wr[0:-1]
            wr = ast.literal_eval(wr)
            winrate = wr / 100
            total_won = round(total_closed * winrate)
            total_closed_counter += total_closed
            total_won_counter += total_won

        return 100 * (total_won_counter / total_closed_counter) if total_closed_counter != 0 else 0

    def convert_to_netprofits_series(self, equity_curve_data_dict):
        netprofits_arr = []
        prev_equity = 0
        for date, equity in equity_curve_data_dict.items():
            netprofit = equity - prev_equity
            netprofits_arr.append(netprofit)
            prev_equity = equity

        return pd.Series(netprofits_arr)

    def populate_model_data(self, model, wfo_testing_data, strategy_run_data, training_id, rows_df, equity_curve_rows_df):
        equity_curve_data_dict = self.concat_equity_curve_data_rows(equity_curve_rows_df)
        netprofits_series = self.convert_to_netprofits_series(equity_curve_data_dict)

        run_key = BacktestRunKey()
        run_key.strategyid = strategy_run_data.strategyid
        run_key.exchange = strategy_run_data.exchange
        run_key.currency_pair = strategy_run_data.currency_pair
        run_key.timeframe = strategy_run_data.timeframe
        run_key.parameters = self.merge_wfo_testing_params(rows_df)
        run_key.wfo_cycle_training_id = training_id

        analyzer_data = BacktestAnalyzerData()
        analyzer_data.wfo_training_period = self.get_df_column_val(rows_df, 0, ColumnName.WFO_TRAINING_PERIOD)
        analyzer_data.wfo_testing_period = self.get_df_column_val(rows_df, 0, ColumnName.WFO_TESTING_PERIOD)
        analyzer_data.trainingdaterange = wfo_testing_data.get_total_training_daterange_str()
        analyzer_data.testingdaterange = wfo_testing_data.get_total_testing_daterange_str()
        analyzer_data.startcash = self.get_df_column_val(rows_df, 0, ColumnName.START_CASH)
        analyzer_data.lot_size = self.get_df_column_val(rows_df, 0, ColumnName.LOT_SIZE)
        analyzer_data.total_closed_trades = self.get_sum_values_val(rows_df, ColumnName.TOTAL_CLOSED_TRADES)
        analyzer_data.net_profit = round(self.get_sum_values_val(rows_df, ColumnName.NET_PROFIT), 8)
        analyzer_data.net_profit_pct = round(100 * analyzer_data.net_profit / analyzer_data.startcash, 2)
        dd_calculator = DrawDownCalculator(analyzer_data.startcash)
        dd_info = dd_calculator.calculate(equity_curve_data_dict)
        analyzer_data.max_drawdown_pct = round(dd_info.max.drawdown, 2)
        analyzer_data.max_drawdown_length = round(dd_info.max.len)
        analyzer_data.net_profit_to_maxdd = round(analyzer_data.net_profit_pct / abs(dd_info.max.drawdown), 2) if analyzer_data.max_drawdown_pct != 0 else 0
        analyzer_data.win_rate_pct = '{}%'.format(round(self.calculate_winrate_pct(rows_df), 2))

        equity_curve_data = EquityCurveData()
        lr_stats = LinearRegressionCalculator.calculate(equity_curve_data_dict)
        equity_curve_data.data = self.get_equitycurve_data(equity_curve_data_dict)
        equity_curve_data.angle = round(lr_stats.angle)
        equity_curve_data.slope = round(lr_stats.slope, 3)
        equity_curve_data.intercept = round(lr_stats.intercept, 3)
        equity_curve_data.rvalue = round(lr_stats.r_value, 3)
        equity_curve_data.rsquaredvalue = round(lr_stats.r_squared, 3)
        equity_curve_data.pvalue = round(lr_stats.p_value, 3)
        equity_curve_data.stderr = round(lr_stats.std_err, 3)

        montecarlo_data = MonteCarloData()
        mcsimulator = MonteCarloSimulator()
        mcsimulation = mcsimulator.calculate(netprofits_series, analyzer_data.startcash)
        montecarlo_data.mc_riskofruin_pct   = self.get_pct_fmt(100 * mcsimulation.risk_of_ruin)
        montecarlo_data.mc_mediandd_pct     = self.get_pct_fmt(100 * mcsimulation.median_dd)
        montecarlo_data.mc_medianreturn_pct = self.get_pct_fmt(100 * mcsimulation.median_return)

        model.add_result_row(run_key, analyzer_data, equity_curve_data, montecarlo_data)

        return model

    def interpolate(self, key, k_arr, v_arr):
        for c in range(1, len(k_arr) + 1):
            prev_k = k_arr[c - 1]
            curr_k = k_arr[c]
            prev_v = v_arr[c - 1]
            curr_v = v_arr[c]
            if key >= prev_k and key <= curr_k:
                return (prev_v + curr_v) / 2
        raise ValueError("Wrong data in interpolate() method: key={}".format(key))

    def calculate_avg(self, key, input_arr):
        arr = []
        for row_arr in input_arr:
            k_arr = row_arr[0]
            v_arr = row_arr[1]
            if key in k_arr:
                key_idx = k_arr.index(key)
                arr.append(v_arr[key_idx])
            else:
                interpolated_val = self.interpolate(key, k_arr, v_arr)
                arr.append(interpolated_val)
        return np.mean(arr)

    def calculate_avg_timeseries(self, df):
        keys_set = set()
        input_arr = []
        avg_dict = dict()
        for index, row in df.iterrows():
            equity_curve_dict = self.get_equity_curve_data_points(row)
            arr = [[0], [0]]
            for k, v in equity_curve_dict.items():
                key_num = int(k)
                keys_set.add(key_num)
                arr[0].append(key_num)
                arr[1].append(v)
            input_arr.append(arr)
        keys_set = sorted(keys_set, key=lambda t: t)
        for key in keys_set:
            avg_val = self.calculate_avg(key, input_arr)
            key_str = str(key)
            avg_dict[key_str] = avg_val

        return dict(sorted(avg_dict.items(), key=lambda t: t[0]))

    def get_avg_total_closed(self, data_dict):
        return len(data_dict.keys())

    def get_avg_net_profit(self, data_dict):
        last_key = list(data_dict.keys())[-1]
        last_val = data_dict[last_key]
        netprofit = last_val
        return netprofit

    def calculate_avg_winrate_pct(self, netprofits_series):
        total_closed = len(netprofits_series)
        total_won = sum(i > 0 for i in list(netprofits_series))
        return 100 * total_won / total_closed

    def populate_avg_model_data(self, model, strategy_run_data, rows_df, equity_curve_rows_df):
        avg_equity_curve_data_dict = self.calculate_avg_timeseries(equity_curve_rows_df)
        netprofits_series = self.convert_to_netprofits_series(avg_equity_curve_data_dict)

        run_key = BacktestRunKey()
        run_key.strategyid = strategy_run_data.strategyid
        run_key.exchange = strategy_run_data.exchange
        run_key.currency_pair = strategy_run_data.currency_pair
        run_key.timeframe = strategy_run_data.timeframe

        analyzer_data = BacktestAnalyzerData()
        analyzer_data.wfo_training_period = self.get_df_column_val(rows_df, 0, ColumnName.WFO_TRAINING_PERIOD)
        analyzer_data.wfo_testing_period = self.get_df_column_val(rows_df, 0, ColumnName.WFO_TESTING_PERIOD)
        analyzer_data.trainingdaterange = self.get_df_column_val(rows_df, 0, ColumnName.TRAINING_DATE_RANGE)
        analyzer_data.testingdaterange = self.get_df_column_val(rows_df, 0, ColumnName.TESTING_DATE_RANGE)
        analyzer_data.startcash = self.get_df_column_val(rows_df, 0, ColumnName.START_CASH)
        analyzer_data.lot_size = self.get_df_column_val(rows_df, 0, ColumnName.LOT_SIZE)
        analyzer_data.total_closed_trades = self.get_avg_total_closed(avg_equity_curve_data_dict)
        analyzer_data.net_profit = self.get_avg_net_profit(avg_equity_curve_data_dict)
        analyzer_data.net_profit_pct = round(100 * analyzer_data.net_profit / analyzer_data.startcash, 2)
        dd_calculator = DrawDownCalculator(analyzer_data.startcash)
        dd_info = dd_calculator.calculate(avg_equity_curve_data_dict)
        analyzer_data.max_drawdown_pct = round(dd_info.max.drawdown, 2)
        analyzer_data.max_drawdown_length = round(dd_info.max.len)
        analyzer_data.net_profit_to_maxdd = round(analyzer_data.net_profit_pct / abs(dd_info.max.drawdown), 2) if analyzer_data.max_drawdown_pct != 0 else 0
        analyzer_data.win_rate_pct = '{}%'.format(round(self.calculate_avg_winrate_pct(netprofits_series), 2))

        equity_curve_data = EquityCurveData()
        lr_stats = LinearRegressionCalculator.calculate(avg_equity_curve_data_dict)
        equity_curve_data.data = self.get_equitycurve_data(avg_equity_curve_data_dict)
        equity_curve_data.angle = round(lr_stats.angle)
        equity_curve_data.rvalue = round(lr_stats.r_value, 3)
        equity_curve_data.rsquaredvalue = round(lr_stats.r_squared, 3)

        model.add_result_row(run_key, analyzer_data, equity_curve_data)
        return model
