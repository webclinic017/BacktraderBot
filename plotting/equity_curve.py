import numpy as np
import talib as ta
from bokeh.layouts import column
from bokeh.models import Span, Label
from bokeh.plotting import figure
from bokeh.io import export_png
from bokeh.models.tickers import FixedTicker
from math import pi
import itertools as it
from datetime import datetime
from bokeh.models import DatetimeTickFormatter
from bokeh.models import NumeralTickFormatter
from config.strategy_config import AppConfig
from model.reports_common import ColumnName
from model.common import StrategyRunData
from datetime import timedelta
from wfo.wfo_helper import WFOHelper
import json
import os
import pandas as pd
import ast


class EquityCurvePlotter(object):
    _EQUITY_CURVE_IMAGE_WIDTH = 1800
    _EQUITY_CURVE_IMAGE_HEIGHT = 800
    _EQUITY_CURVE_SMA1_LENGTH = 20
    _EQUITY_CURVE_SMA2_LENGTH = 40

    _PALETTE = ['#2ca02c', '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5', '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78']

    def __init__(self, step_name):
        self._step_name = step_name

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_output_equity_curve_images_path(self, base_dir, args):
        return '{}/strategyrun_results/{}/{}_EquityCurveImages'.format(base_dir, args.runid, self._step_name)

    def get_output_image_filename_common(self, base_path, strategy_run_data, image_counter):
        return "{}/{:04d}-{}-{}-{}-{}.png".format(base_path, image_counter, strategy_run_data.strategyid, strategy_run_data.exchange, strategy_run_data.currency_pair, strategy_run_data.timeframe)

    def get_output_image_filename_step1(self, base_path, strategy_run_data, wfo_cycle_id, wfo_cycle_training_id):
        return "{}/{}-{}-{}-{}-{:02d}-{:04d}.png".format(base_path, strategy_run_data.strategyid, strategy_run_data.exchange, strategy_run_data.currency_pair, strategy_run_data.timeframe, wfo_cycle_id, wfo_cycle_training_id)

    def get_portfolio_output_image_filename(self, base_path):
        return "{}/Portfolio_Strategy_Equity_Curve.png".format(base_path)

    def build_x_axis_line(self, value, color):
        return Span(location=value, dimension='height', line_color=color, line_dash='dashed', line_width=1, line_alpha=0.8)

    def build_y_axis_zero_line(self):
        return Span(location=0, dimension='width', line_color='blue', line_dash='dashed', line_width=1, line_alpha=0.8)

    def get_x_axis_formatter(self, x_axis_flag):
        if x_axis_flag:
            return NumeralTickFormatter(format="0")
        else:
            return DatetimeTickFormatter(
                days=["%Y-%m-%d %H:%M"],
                months=["%Y-%m-%d %H:%M"],
                hours=["%Y-%m-%d %H:%M"],
                minutes=["%Y-%m-%d %H:%M"]
            )

    def get_x_axis_label(self, x_axis_flag):
        if x_axis_flag is True:
            return "Trade Number"
        else:
            return "Trade Date"

    def initialize_dirs(self, args):
        base_dir = self.whereAmI()
        output_path = self.get_output_equity_curve_images_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)
        return output_path

    def build_equity_curve_plot_figure(self, x_data):
        x_axis_flag = AppConfig.is_global_equitycurve_img_x_axis_trades()
        equity_curve_plot = figure(plot_height=self._EQUITY_CURVE_IMAGE_HEIGHT, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, tools="", x_axis_type="datetime",
                                   toolbar_location=None, x_axis_label=self.get_x_axis_label(x_axis_flag), x_axis_location="below",
                                   y_axis_label="Equity", background_fill_color="#efefef")
        equity_curve_plot.xaxis.formatter = self.get_x_axis_formatter(x_axis_flag)
        if not x_axis_flag:
            x_data_ticks = []
            for x in x_data:
                x_data_ticks.append(int(x.timestamp() * 1000))
            equity_curve_plot.xaxis.ticker = FixedTicker(ticks=list(x_data_ticks))
            equity_curve_plot.xaxis.major_label_orientation = pi/4
        equity_curve_plot.yaxis.formatter = NumeralTickFormatter(format="0")
        equity_curve_plot.title.text_font_style = "normal"
        equity_curve_plot.add_layout(self.build_y_axis_zero_line())
        return equity_curve_plot

    def get_equity_data_x_axis(self, arr):
        if AppConfig.is_global_equitycurve_img_x_axis_trades():
            return self.get_equity_data_x_axis_as_trades(arr)
        else:
            return self.get_equity_data_x_axis_as_dates(arr)

    def get_equity_data_x_axis_as_dates(self, arr):
        counter = 1
        process_arr = list(arr)
        result = []
        for eq_date_str in process_arr:
            eq_date = datetime.strptime(eq_date_str, '%y%m%d%H%M')
            eq_date = pd.to_datetime(eq_date)
            result.append(eq_date)
            counter += 1
        return result

    def get_equity_data_x_axis_as_trades(self, arr):
        counter = 1
        process_arr = list(arr)
        result = []
        for item in process_arr:
            result.append(counter)
            counter += 1
        return result

    def get_equity_data_y_axis(self, equity_data_arr):
        result = []
        result.extend(list(equity_data_arr))
        return result

    def adjust_fwtest_data_by_startcash(self, fwtest_y_data, startcash):
        return [x + startcash for x in fwtest_y_data]

    def get_equity_curve_data_points_common(self, equity_curve_df, strategy_run_data, parameters_str):
        return equity_curve_df.loc[[(strategy_run_data.strategyid, strategy_run_data.exchange, strategy_run_data.currency_pair, strategy_run_data.timeframe, parameters_str)], ColumnName.EQUITY_CURVE_DATA_POINTS].values[0]

    def get_equity_curve_data_points_step1(self, equity_curve_df, strategy_run_data, wfo_cycle_id, wfo_cycle_training_id):
        df = equity_curve_df.loc[[(strategy_run_data.strategyid, strategy_run_data.exchange, strategy_run_data.currency_pair, strategy_run_data.timeframe)]]
        df = df.loc[(df[ColumnName.WFO_CYCLE_ID] == wfo_cycle_id) & (df[ColumnName.WFO_CYCLE_TRAINING_ID] == wfo_cycle_training_id)]
        return df[ColumnName.EQUITY_CURVE_DATA_POINTS].values[0]

    def get_linear_regression_line_points(self, x_axis_data, equitycurveslope, equitycurveintercept, startcash):
        x1 = x_axis_data[0]
        y1 = startcash + equitycurveintercept
        xn = x_axis_data[-1]
        yn = startcash + equitycurveintercept + len(x_axis_data) * equitycurveslope
        return [[x1, xn], [y1, yn]]

    def get_equity_curve_sma_points(self, period, equity_curve_y_axis_data):
        result = []
        arr = np.array([float(x) for x in equity_curve_y_axis_data])
        calc_sma_data = list(ta.SMA(arr, period))
        calc_sma_data = [float(x) for x in calc_sma_data]
        result.extend(calc_sma_data)
        return result

    def is_possible_to_draw_sma(self, x_data_arr, sma_length):
        return len(x_data_arr) > sma_length

    def build_plot_label(self, y_coord, txt):
        return Label(x=10, y=y_coord, x_units='screen', y_units='screen', text=txt, text_font_size="10pt", render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)

    def get_column_value_by_name(self, row, name):
        return row[name]

    def create_text_lines(self, row):
        text_lines_arr = []
        strategy_str         = self.get_column_value_by_name(row, ColumnName.STRATEGY_ID)
        exchange_str         = self.get_column_value_by_name(row, ColumnName.EXCHANGE)
        symbol_str           = self.get_column_value_by_name(row, ColumnName.CURRENCY_PAIR)
        timeframe_str        = self.get_column_value_by_name(row, ColumnName.TIMEFRAME)
        parameters_str       = self.get_column_value_by_name(row, ColumnName.PARAMETERS)
        text_lines_arr.append("{}, {}, {}, {}".format(strategy_str, exchange_str, symbol_str, timeframe_str))
        text_lines_arr.append("Parameters: {}".format(parameters_str))

        wfo_cycle_id             = self.get_column_value_by_name(row, ColumnName.WFO_CYCLE_ID)
        wfo_cycle_training_id    = self.get_column_value_by_name(row, ColumnName.WFO_CYCLE_TRAINING_ID)
        wfo_training_period_str  = self.get_column_value_by_name(row, ColumnName.WFO_TRAINING_PERIOD)
        wfo_testing_period_str   = self.get_column_value_by_name(row, ColumnName.WFO_TESTING_PERIOD)
        trainingdaterange_str    = self.get_column_value_by_name(row, ColumnName.TRAINING_DATE_RANGE)
        testingdaterange_str     = self.get_column_value_by_name(row, ColumnName.TESTING_DATE_RANGE)
        text_lines_arr.append("WFO Cycle ID: {}, WFO Cycle Training ID: {}, WFO Training Period: {}, WFO Testing Period: {}, Training Date Range: {}, Testing Date Range: {}".format(wfo_cycle_id, wfo_cycle_training_id, wfo_training_period_str, wfo_testing_period_str, trainingdaterange_str, testingdaterange_str))

        startcash_str            = round(self.get_column_value_by_name(row, ColumnName.START_CASH))
        total_closed_trades      = self.get_column_value_by_name(row, ColumnName.TOTAL_CLOSED_TRADES)
        net_profit               = round(self.get_column_value_by_name(row, ColumnName.NET_PROFIT))
        net_profit_pct           = self.get_column_value_by_name(row, ColumnName.NET_PROFIT_PCT)
        max_drawdown_pct         = self.get_column_value_by_name(row, ColumnName.MAX_DRAWDOWN_PCT)
        max_drawdown_length      = self.get_column_value_by_name(row, ColumnName.MAX_DRAWDOWN_LENGTH)
        text_lines_arr.append("Start Cash: {}, Total Closed Trades: {}, Net Profit: {}, Net Profit,%: {}%, Max Drawdown,%: {}%, Max Drawdown Length: {}".format(startcash_str, total_closed_trades, net_profit, net_profit_pct, max_drawdown_pct, max_drawdown_length))

        net_profit_to_maxdd      = self.get_column_value_by_name(row, ColumnName.NET_PROFIT_TO_MAX_DRAWDOWN)
        win_rate_pct             = self.get_column_value_by_name(row, ColumnName.WIN_RATE_PCT)
        winning_months_pct       = self.get_column_value_by_name(row, ColumnName.WINNING_MONTHS_PCT)
        profit_factor            = round(self.get_column_value_by_name(row, ColumnName.PROFIT_FACTOR), 3)
        sqn                      = self.get_column_value_by_name(row, ColumnName.SQN)
        mc_riskofruin_pct        = self.get_column_value_by_name(row, ColumnName.MC_RISK_OF_RUIN_PCT)
        text_lines_arr.append("Net Profit To Max Drawdown: {}, Win Rate,%: {}, Winning Months,%: {}%, Profit Factor: {}, SQN: {}, MC Risk Of Ruin, %: {}".format(net_profit_to_maxdd, win_rate_pct, winning_months_pct, profit_factor, sqn, mc_riskofruin_pct))

        equitycurveangle         = self.get_column_value_by_name(row, ColumnName.EQUITY_CURVE_ANGLE)
        equitycurveslope         = round(self.get_column_value_by_name(row, ColumnName.EQUITY_CURVE_SLOPE), 3)
        equitycurveintercept     = round(self.get_column_value_by_name(row, ColumnName.EQUITY_CURVE_INTERCEPT), 3)
        equitycurvervalue        = round(self.get_column_value_by_name(row, ColumnName.EQUITY_CURVE_R_VALUE), 3)
        equitycurversquaredvalue = round(self.get_column_value_by_name(row, ColumnName.EQUITY_CURVE_R_SQUARED_VALUE), 3)
        equitycurvepvalue        = round(self.get_column_value_by_name(row, ColumnName.EQUITY_CURVE_P_VALUE), 3)
        equitycurvestderr        = round(self.get_column_value_by_name(row, ColumnName.EQUITY_CURVE_STDERR), 3)
        text_lines_arr.append("Equity Curve Angle={}°, Equity Curve Slope={}, Equity Curve Intercept={}, Equity Curve R-value={}, Equity Curve R-Squared value={}, Equity Curve P-value={}, Equity Curve Stderr={}".format(equitycurveangle, equitycurveslope, equitycurveintercept, equitycurvervalue, equitycurversquaredvalue, equitycurvepvalue, equitycurvestderr))

        return text_lines_arr

    def build_description(self, row):
        start_text_y_coord = 110
        result = figure(tools="", toolbar_location=None, plot_height=start_text_y_coord + 40, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, x_axis_location="above")

        text_lines_arr = self.create_text_lines(row)
        result.add_layout(self.build_plot_label(start_text_y_coord - 0 * 20, text_lines_arr[0]))
        result.add_layout(self.build_plot_label(start_text_y_coord - 1 * 20, text_lines_arr[1]))
        result.add_layout(self.build_plot_label(start_text_y_coord - 2 * 20, text_lines_arr[2]))
        result.add_layout(self.build_plot_label(start_text_y_coord - 3 * 20, text_lines_arr[3]))
        result.add_layout(self.build_plot_label(start_text_y_coord - 4 * 20, text_lines_arr[4]))
        result.add_layout(self.build_plot_label(start_text_y_coord - 5 * 20, text_lines_arr[5]))

        return result

    def draw_equity_curve(self, row, equity_curve_data_points_str, equitycurveslope, equitycurveintercept):
        description = self.build_description(row)

        equity_curve_data_points_dict = json.loads(equity_curve_data_points_str)
        x_data = self.get_equity_data_x_axis(equity_curve_data_points_dict.keys())
        y_data = self.get_equity_data_y_axis(equity_curve_data_points_dict.values())
        equity_curve_plot = self.build_equity_curve_plot_figure(x_data)
        equity_curve_plot.line(x_data, y_data, line_width=3, alpha=0.7, legend_label='Equity curve')

        lr_points = self.get_linear_regression_line_points(x_data, equitycurveslope, equitycurveintercept, 0)
        equity_curve_plot.line(lr_points[0], lr_points[1], line_width=1, line_color="red", alpha=0.5, legend_label='Linear regression')

        if self.is_possible_to_draw_sma(x_data, self._EQUITY_CURVE_SMA1_LENGTH):
            equity_curve_sma1_y_data = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA1_LENGTH, y_data)
            equity_curve_plot.line(x_data, equity_curve_sma1_y_data, color='orange', line_width=1, alpha=0.7, legend_label='Equity curve SMA({})'.format(self._EQUITY_CURVE_SMA1_LENGTH))

        if self.is_possible_to_draw_sma(x_data, self._EQUITY_CURVE_SMA2_LENGTH):
            equity_curve_sma2_y_data = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA2_LENGTH, y_data)
            equity_curve_plot.line(x_data, equity_curve_sma2_y_data, color='magenta', line_width=1, alpha=0.5, legend_label='Equity curve SMA({})'.format(self._EQUITY_CURVE_SMA2_LENGTH))
        equity_curve_plot.legend.location = "top_left"

        return column(description, equity_curve_plot)

    def get_parameters_map(self, parameters_json):
        return ast.literal_eval(parameters_json)

    def generate_images_common(self, results_df, equity_curve_df, args):
        image_counter = 0
        output_path = self.initialize_dirs(args)
        print("Rendering {} equity curve images into {}".format(len(results_df), output_path))
        for index, row in results_df.iterrows():
            strategy_run_data = StrategyRunData(row[ColumnName.STRATEGY_ID], row[ColumnName.EXCHANGE], row[ColumnName.CURRENCY_PAIR], row[ColumnName.TIMEFRAME])
            parameters_str = row[ColumnName.PARAMETERS]
            equitycurveslope = round(row[ColumnName.EQUITY_CURVE_SLOPE], 3)
            equitycurveintercept = round(row[ColumnName.EQUITY_CURVE_INTERCEPT], 3)
            equity_curve_data_points_str = self.get_equity_curve_data_points_common(equity_curve_df, strategy_run_data, parameters_str)
            img = self.draw_equity_curve(row, equity_curve_data_points_str, equitycurveslope, equitycurveintercept)
            image_counter += 1
            if image_counter % 10 == 0 or image_counter == len(results_df):
                print("Rendered {} equity curve images...".format(image_counter))
            image_filename = self.get_output_image_filename_common(output_path, strategy_run_data, image_counter)
            export_png(img, filename=image_filename)

    def deltas_to_absolute_netprofit(self, y_data):
        sum_value = 0
        result = []
        for val in y_data:
            sum_value += val
            result.append(sum_value)
        return result

    def absolute_to_deltas_netprofit(self, y_data):
        counter = it.count()
        result = [0]
        for val in y_data:
            idx = next(counter)
            if idx > 0:
                result.append(val - y_data[idx - 1])
        return result

    def merge_plot_data(self, combined_data_dict, x_data, y_data):
        deltas_y_data = self.absolute_to_deltas_netprofit(y_data)
        whole_data_dict = dict(zip(x_data, deltas_y_data))
        for key, val in whole_data_dict.items():
            if key not in combined_data_dict.keys():
                combined_data_dict[key] = val
            else:
                combined_data_dict[key] = combined_data_dict[key] + val

        return combined_data_dict

    def build_generic_data_plot_figure(self, x_label, y_label):
        data_plot = figure(plot_height=self._EQUITY_CURVE_IMAGE_HEIGHT, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, tools="", x_axis_type="datetime",
                           toolbar_location=None, x_axis_label=x_label, x_axis_location="below",
                           y_axis_label=y_label, background_fill_color="#efefef")
        data_plot.xaxis.formatter = self.get_x_axis_formatter(True)
        data_plot.yaxis.formatter = NumeralTickFormatter(format="0")
        data_plot.title.text_font_style = "normal"
        data_plot.add_layout(self.build_y_axis_zero_line())
        return data_plot

    def generate_generic_data_image(self, output_path, arr):
        print("Rendering data image into {}".format(output_path))
        x_data = self.get_equity_data_x_axis_as_trades(arr)
        x_data = x_data[1:]
        y_data = self.get_equity_data_y_axis(arr)

        data_plot = self.build_generic_data_plot_figure("Time", "Price")
        data_plot.line(x_data, y_data, line_width=3, alpha=0.7, legend_label='Price')
        img = column(data_plot)
        export_png(img, filename=output_path)

    def build_equity_curve_plot_figure_step3(self, x_data):
        equity_curve_plot = figure(plot_height=self._EQUITY_CURVE_IMAGE_HEIGHT, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, tools="", x_axis_type="datetime",
                                   toolbar_location=None, x_axis_label=self.get_x_axis_label(False), x_axis_location="below",
                                   y_axis_label="Equity", background_fill_color="#efefef")
        equity_curve_plot.xaxis.formatter = self.get_x_axis_formatter(False)
        x_data_ticks = []
        for x in x_data:
            x_data_ticks.append(int(x.timestamp() * 1000))
        equity_curve_plot.xaxis.ticker = FixedTicker(ticks=list(x_data_ticks))
        equity_curve_plot.xaxis.major_label_orientation = pi/4
        equity_curve_plot.yaxis.formatter = NumeralTickFormatter(format="0")
        equity_curve_plot.title.text_font_style = "normal"
        equity_curve_plot.add_layout(self.build_y_axis_zero_line())
        return equity_curve_plot

    def get_wfo_cycles_boundaries(self, wfo_cycles_list):
        dt_boundaries = [pd.to_datetime(wfo_cycle.testing_start_date) for wfo_cycle in wfo_cycles_list]
        last_entry_dt = wfo_cycles_list[-1].testing_end_date
        last_entry_dt += timedelta(days=1)
        dt_boundaries.append(pd.to_datetime(last_entry_dt))
        return dt_boundaries

    def get_boundary_trade_num(self, x_data_index, boundary_dt):
        prev_dt = 0
        prev_trade_num = 0
        boundary_dt_tstamp = boundary_dt.timestamp()
        for curr_dt, trade_num in x_data_index.items():
            curr_dt_tstamp = curr_dt.timestamp()
            if boundary_dt_tstamp >= prev_dt and boundary_dt_tstamp <= curr_dt_tstamp:
                if prev_dt == 0:
                    return trade_num
                else:
                    return prev_trade_num
            prev_dt = curr_dt_tstamp
            prev_trade_num = trade_num
        last_entry = list(x_data_index.items())[-1]
        if boundary_dt_tstamp > last_entry[0].timestamp():
            return last_entry[1]

    def draw_wfo_cycles_boundaries(self, x_axis_flag, x_data_index, wfo_testing_data_list, equity_curve_plot):
        wfo_cycles_list = wfo_testing_data_list.get_wfo_cycles_list()
        wfo_cycle_boundaries = self.get_wfo_cycles_boundaries(wfo_cycles_list)
        for boundary_dt in wfo_cycle_boundaries:
            if x_axis_flag:
                val = self.get_boundary_trade_num(x_data_index, boundary_dt)
            else:
                val = int(boundary_dt.timestamp() * 1000)
            equity_curve_plot.add_layout(self.build_x_axis_line(val, "red"))
        return equity_curve_plot

    def get_step3_x_data_index(self, data_points_dict):
        x_data_trades = self.get_equity_data_x_axis_as_trades(data_points_dict.keys())
        x_data_dates = self.get_equity_data_x_axis_as_dates(data_points_dict.keys())
        x_data = dict(zip(x_data_dates, x_data_trades))
        return x_data

    def get_step3_x_data_from_index(self, x_axis_flag, x_data_index, x_data_keys_str_arr):
        result_arr = list()
        x_data_keys_date_arr = self.get_equity_data_x_axis_as_dates(x_data_keys_str_arr)
        for date_key in x_data_keys_date_arr:
            if date_key in x_data_index:
                if x_axis_flag:
                    result_arr.append(x_data_index[date_key])
                else:
                    result_arr.append(date_key)
        return result_arr

    def draw_step3_equity_curves(self, wfo_testing_data_list, strategy_run_data, rows_df, avg_row_df):
        x_axis_flag = AppConfig.is_global_equitycurve_img_x_axis_trades()
        avg_row = avg_row_df.iloc[0]
        data_points_dict = json.loads(avg_row[ColumnName.EQUITY_CURVE_DATA_POINTS])
        x_data_index = self.get_step3_x_data_index(data_points_dict)

        x_data = self.get_step3_x_data_from_index(x_axis_flag, x_data_index, data_points_dict.keys())
        y_data = self.get_equity_data_y_axis(data_points_dict.values())

        equity_curve_plot = self.build_equity_curve_plot_figure(x_data)

        equity_curve_plot.line(x_data, y_data, line_width=6, alpha=1, color='red', legend_label='Average')

        equity_curve_plot = self.draw_wfo_cycles_boundaries(x_axis_flag, x_data_index, wfo_testing_data_list, equity_curve_plot)

        c = 0
        for index, row in rows_df.iterrows():
            data_points_dict = json.loads(row[ColumnName.EQUITY_CURVE_DATA_POINTS])
            x_data = self.get_step3_x_data_from_index(x_axis_flag, x_data_index, data_points_dict.keys())
            y_data = self.get_equity_data_y_axis(data_points_dict.values())
            wfo_cycle_training_id = row[ColumnName.WFO_CYCLE_TRAINING_ID]
            l_width = 6 if c == 0 else 2
            equity_curve_plot.line(x_data, y_data, line_width=l_width, alpha=0.7, color=self._PALETTE[c], legend_label='{}: {}, {}, {}, {}'.format(
                wfo_cycle_training_id, strategy_run_data.strategyid, strategy_run_data.exchange, strategy_run_data.currency_pair, strategy_run_data.timeframe))
            c += 1

        equity_curve_plot.legend.location = "bottom_left"
        return column(equity_curve_plot)

    def generate_images_step1(self, results_df, equity_curve_df, args):
        image_counter = 0
        output_path = self.initialize_dirs(args)
        print("Rendering {} equity curve images into {}".format(len(results_df), output_path))
        for index, row in results_df.iterrows():
            strategy_run_data = StrategyRunData(row[ColumnName.STRATEGY_ID], row[ColumnName.EXCHANGE], row[ColumnName.CURRENCY_PAIR], row[ColumnName.TIMEFRAME])
            wfo_cycle_id = row[ColumnName.WFO_CYCLE_ID]
            wfo_cycle_training_id = row[ColumnName.WFO_CYCLE_TRAINING_ID]
            equity_curve_data_points_str = self.get_equity_curve_data_points_step1(equity_curve_df, strategy_run_data, wfo_cycle_id, wfo_cycle_training_id)

            equitycurveslope = round(row[ColumnName.EQUITY_CURVE_SLOPE], 3)
            equitycurveintercept = round(row[ColumnName.EQUITY_CURVE_INTERCEPT], 3)
            img = self.draw_equity_curve(row, equity_curve_data_points_str, equitycurveslope, equitycurveintercept)
            image_counter += 1
            if image_counter % 10 == 0 or image_counter == len(results_df):
                print("Rendered {} equity curve images...".format(image_counter))
            image_filename = self.get_output_image_filename_step1(output_path, strategy_run_data, wfo_cycle_id, wfo_cycle_training_id)
            export_png(img, filename=image_filename)

    def generate_images_step3(self, wfo_testing_data_list, step3_model_df, step3_equity_curve_model_df, step3_avg_equity_curve_model_df, args):
        output_path = self.initialize_dirs(args)
        strat_list, exc_list, sym_list, tf_list = WFOHelper.get_unique_index_value_lists(step3_model_df)
        print("Rendering WFO Step3 equity curve images into {}".format(output_path))

        image_counter = 0
        for strategy in strat_list:
            for exchange in exc_list:
                for symbol in sym_list:
                    for timeframe in tf_list:
                        strategy_run_data = StrategyRunData(strategy, exchange, symbol, timeframe)
                        rows_df = step3_equity_curve_model_df.loc[[(strategy, exchange, symbol, timeframe)]]
                        avg_rows_df = step3_avg_equity_curve_model_df.loc[[(strategy, exchange, symbol, timeframe)]]
                        img = self.draw_step3_equity_curves(wfo_testing_data_list, strategy_run_data, rows_df, avg_rows_df)
                        image_counter += 1
                        if image_counter % 10 == 0 or image_counter == len(step3_equity_curve_model_df):
                            print("Rendered {} equity curve images...".format(image_counter))
                        image_filename = self.get_output_image_filename_common(output_path, strategy_run_data, image_counter)
                        export_png(img, filename=image_filename)

