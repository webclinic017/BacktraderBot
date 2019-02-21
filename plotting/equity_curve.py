import numpy as np
import talib as ta
from bokeh.layouts import column
from bokeh.models import Span, Label
from bokeh.plotting import figure
from bokeh.io import export_png
from datetime import datetime
from bokeh.models import DatetimeTickFormatter
from bokeh.models import NumeralTickFormatter
from datetime import timedelta
import json
import os
import pandas as pd


class EquityCurvePlotter(object):

    _step_name = None

    _EQUITY_CURVE_IMAGE_WIDTH = 1500
    _EQUITY_CURVE_IMAGE_HEIGHT = 800
    _EQUITY_CURVE_SMA1_LENGTH = 7
    _EQUITY_CURVE_SMA2_LENGTH = 14

    def __init__(self, step_name):
        self._step_name = step_name

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_output_equity_curve_images_path(self, base_dir, args):
        return '{}/strategyrun_results/{}/{}_EquityCurveImages'.format(base_dir, args.runid, self._step_name)

    def get_output_image_filename(self, base_path, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, image_counter):
        return "{}/{:04d}-{}-{}-{}-{}.png".format(base_path, image_counter, strategy_id_data_str, exchange_str, symbol_str, timeframe_str)

    def build_y_axis_zero_line(self):
        return Span(location=0, dimension='width', line_color='blue', line_dash='dashed', line_width=1, line_alpha=0.8)

    def build_equity_curve_plot_figure(self):
        equity_curve_plot = figure(plot_height=self._EQUITY_CURVE_IMAGE_HEIGHT, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, tools="", x_axis_type="datetime",
                                   toolbar_location=None, x_axis_label="Trade Date", x_axis_location="below",
                                   y_axis_label="Equity", background_fill_color="#efefef")
        equity_curve_plot.xaxis.formatter = DatetimeTickFormatter(
            days=["%Y-%m-%d"],
            months=["%Y-%m-%d"],
            hours=["%Y-%m-%d"],
            minutes=["%Y-%m-%d"]
        )
        equity_curve_plot.yaxis.formatter = NumeralTickFormatter(format="0")
        equity_curve_plot.title.text_font_style = "normal"
        equity_curve_plot.add_layout(self.build_y_axis_zero_line())
        return equity_curve_plot

    def get_equity_curve_dates(self, dates_arr, prepend_start_date):
        counter = 1
        dates_arr = list(dates_arr)
        first_date = datetime.strptime(dates_arr[0], '%y%m%d%H%M')
        first_date = pd.to_datetime(first_date)
        start_date = first_date - timedelta(days=1)
        result = [prepend_start_date] if prepend_start_date is not None else [start_date]
        for eq_date_str in dates_arr:
            eq_date = datetime.strptime(eq_date_str, '%y%m%d%H%M')
            eq_date = pd.to_datetime(eq_date)
            result.append(eq_date)
            counter += 1
        return result

    def get_equity_data(self, equity_data_arr, prepend_value):
        result = [prepend_value] if prepend_value is not None else []
        result.extend(list(equity_data_arr))
        return result

    def adjust_fwtest_data_by_startcash(self, fwtest_y_data, startcash):
        return [x + startcash for x in fwtest_y_data]

    def get_equity_curve_data_points(self, equity_curve_df, strategy_str, exchange_str, symbol_str, timeframe_str, parameters_str):
        return equity_curve_df.loc[(strategy_str, exchange_str, symbol_str, timeframe_str, parameters_str), "Equity Curve Data Points"]

    def get_linear_regression_points(self, x_axis_data, equitycurveslope, equitycurveintercept, startcash):
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

    def get_column_value_by_name(self, row, name, prefix, is_fwtest):
        result = row[name]
        if is_fwtest:
            column_name = "{}: {}".format(prefix, name)
            result = row[column_name]
        return result

    def build_description(self, row, prefix, is_fwtest):
        result = figure(tools="", toolbar_location=None, plot_height=150, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, x_axis_location="above")

        strategy_str         = self.get_column_value_by_name(row, 'Strategy ID', prefix, False)
        exchange_str         = self.get_column_value_by_name(row, 'Exchange', prefix, False)
        symbol_str           = self.get_column_value_by_name(row, 'Currency Pair', prefix, False)
        timeframe_str        = self.get_column_value_by_name(row, 'Timeframe', prefix, False)
        date_range_str       = self.get_column_value_by_name(row, 'Date Range', prefix, is_fwtest)
        startcash_str        = self.get_column_value_by_name(row, 'Start Cash', prefix, is_fwtest)
        parameters_str       = self.get_column_value_by_name(row, 'Parameters', prefix, False)
        total_closed_trades  = self.get_column_value_by_name(row, 'Total Closed Trades', prefix, is_fwtest)
        net_profit_pct       = self.get_column_value_by_name(row, 'Net Profit, %', prefix, is_fwtest)
        max_drawdown_pct     = self.get_column_value_by_name(row, 'Max Drawdown, %', prefix, is_fwtest)
        max_drawdown_length  = self.get_column_value_by_name(row, 'Max Drawdown Length', prefix, is_fwtest)
        win_rate_pct         = self.get_column_value_by_name(row, 'Win Rate, %', prefix, is_fwtest)
        winning_months_pct   = self.get_column_value_by_name(row, 'Winning Months, %', prefix, is_fwtest)
        profit_factor        = self.get_column_value_by_name(row, 'Profit Factor', prefix, is_fwtest)
        sqn                  = self.get_column_value_by_name(row, 'SQN', prefix, is_fwtest)
        equitycurveangle     = self.get_column_value_by_name(row, 'Equity Curve Angle', prefix, is_fwtest)
        equitycurveslope     = round(self.get_column_value_by_name(row, 'Equity Curve Slope', prefix, is_fwtest), 3)
        equitycurveintercept = round(self.get_column_value_by_name(row, 'Equity Curve Intercept', prefix, is_fwtest), 3)
        equitycurvervalue    = round(self.get_column_value_by_name(row, 'Equity Curve R-value', prefix, is_fwtest), 3)
        equitycurvepvalue    = round(self.get_column_value_by_name(row, 'Equity Curve P-value', prefix, is_fwtest), 3)
        equitycurvestderr    = round(self.get_column_value_by_name(row, 'Equity Curve Stderr', prefix, is_fwtest), 3)
        text1 = "{}, {}, {}, {}, {}, {}".format(strategy_str, exchange_str, symbol_str, timeframe_str, date_range_str, startcash_str)
        text2 = "Parameters: {}".format(parameters_str)
        text3 = "{} Start Cash: {}, {} Total Closed Trades: {}, {} Net Profit,%: {}%, {} Max Drawdown,%: {}%, {} Max Drawdown Length: {}, {} Win Rate,%: {}".format(prefix, startcash_str, prefix, total_closed_trades, prefix, net_profit_pct, prefix, max_drawdown_pct, prefix, max_drawdown_length, prefix, win_rate_pct)
        text4 = "{} Winning Months,%: {}%, {} Profit Factor: {}, {} SQN: {}".format(prefix, winning_months_pct, prefix, profit_factor, prefix, sqn)
        text5 = "{} Equity Curve Angle={}°, {} Equity Curve Slope={}, {} Equity Curve Intercept={}, {} Equity Curve R-value={}, {} Equity Curve P-value={}, {} Equity Curve Stderr={}".format(prefix, equitycurveangle, prefix, equitycurveslope, prefix, equitycurveintercept, prefix, equitycurvervalue, prefix, equitycurvepvalue, prefix, equitycurvestderr)

        result.add_layout(self.build_plot_label(110, text1))
        result.add_layout(self.build_plot_label(90, text2))
        result.add_layout(self.build_plot_label(70, text3))
        result.add_layout(self.build_plot_label(50, text4))
        result.add_layout(self.build_plot_label(30, text5))
        result.add_layout(self.build_plot_label(10, ""))
        return result

    def draw_equity_curve(self, row, equity_curve_data_points_str, equitycurveslope, equitycurveintercept):
        plot_name_prefix = "BkTest"
        equity_curve_plot = self.build_equity_curve_plot_figure()

        description = self.build_description(row, plot_name_prefix, False)

        equity_curve_data_points_dict = json.loads(equity_curve_data_points_str)
        x_data = self.get_equity_curve_dates(equity_curve_data_points_dict.keys(), None)
        y_data = self.get_equity_data(equity_curve_data_points_dict.values(), 0)
        equity_curve_plot.line(x_data, y_data, line_width=3, alpha=0.7, legend='{} equity curve'.format(plot_name_prefix))

        lr_points = self.get_linear_regression_points(x_data, equitycurveslope, equitycurveintercept, 0)
        equity_curve_plot.line(lr_points[0], lr_points[1], line_width=1, line_color="red", alpha=0.5, legend='{} linear regression'.format(plot_name_prefix))

        if self.is_possible_to_draw_sma(x_data, self._EQUITY_CURVE_SMA1_LENGTH):
            equity_curve_sma1_y_data = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA1_LENGTH, y_data)
            equity_curve_plot.line(x_data, equity_curve_sma1_y_data, color='orange', line_width=1, alpha=0.7, legend='{} equity curve SMA({})'.format(plot_name_prefix, self._EQUITY_CURVE_SMA1_LENGTH))

        if self.is_possible_to_draw_sma(x_data, self._EQUITY_CURVE_SMA2_LENGTH):
            equity_curve_sma2_y_data = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA2_LENGTH, y_data)
            equity_curve_plot.line(x_data, equity_curve_sma2_y_data, color='magenta', line_width=1, alpha=0.5, legend='{} equity curve SMA({})'.format(plot_name_prefix, self._EQUITY_CURVE_SMA2_LENGTH))
        equity_curve_plot.legend.location = "bottom_right"

        return column(description, equity_curve_plot)

    def draw_combined_equity_curves(self, row, bktest_equity_curve_data_points_str, fwtest_equity_curve_data_points_str):
        plot_name_prefix = "FwTest"
        equity_curve_plot = self.build_equity_curve_plot_figure()

        description = self.build_description(row, plot_name_prefix, True)

        bktest_equity_curve_data_points_dict = json.loads(bktest_equity_curve_data_points_str)
        bktest_x_data = self.get_equity_curve_dates(bktest_equity_curve_data_points_dict.keys(), None)
        bktest_y_data = self.get_equity_data(bktest_equity_curve_data_points_dict.values(), 0)
        equity_curve_plot.line(bktest_x_data, bktest_y_data, line_width=3, alpha=0.7, legend='{} equity curve'.format("BkTest"))

        fwtest_equity_curve_data_points_dict = json.loads(fwtest_equity_curve_data_points_str)
        fwtest_x_data = self.get_equity_curve_dates(fwtest_equity_curve_data_points_dict.keys(), bktest_x_data[-1])
        fwtest_y_data = self.get_equity_data(fwtest_equity_curve_data_points_dict.values(), 0)
        fwtest_startcash = bktest_y_data[-1]
        fwtest_y_data = self.adjust_fwtest_data_by_startcash(fwtest_y_data, fwtest_startcash)
        equity_curve_plot.line(fwtest_x_data, fwtest_y_data, line_width=3, alpha=1, legend='{} equity curve'.format(plot_name_prefix), color="mediumseagreen")

        equitycurveslope = self.get_column_value_by_name(row, 'Equity Curve Slope', "", False)
        equitycurveintercept = self.get_column_value_by_name(row, 'Equity Curve Intercept', "", False)
        lr_points = self.get_linear_regression_points(bktest_x_data, equitycurveslope, equitycurveintercept, 0)
        equity_curve_plot.line(lr_points[0], lr_points[1], line_width=1, line_color="red", alpha=0.5, legend='BkTest linear regression')

        equitycurveslope = self.get_column_value_by_name(row, 'Equity Curve Slope', plot_name_prefix, True)
        equitycurveintercept = self.get_column_value_by_name(row, 'Equity Curve Intercept', plot_name_prefix, True)
        lr_points = self.get_linear_regression_points(fwtest_x_data, equitycurveslope, equitycurveintercept, fwtest_startcash)
        equity_curve_plot.line(lr_points[0], lr_points[1], line_width=1, line_color="red", alpha=0.5, legend='{} linear regression'.format(plot_name_prefix))

        combined_x_data = bktest_x_data.copy()
        combined_y_data = bktest_y_data.copy()
        combined_x_data.extend(fwtest_x_data[:-1])
        combined_y_data.extend(fwtest_y_data[:-1])
        if self.is_possible_to_draw_sma(combined_x_data, self._EQUITY_CURVE_SMA1_LENGTH):
            equity_curve_sma1_y_data = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA1_LENGTH, combined_y_data)
            equity_curve_plot.line(combined_x_data, equity_curve_sma1_y_data, color='orange', line_width=1, alpha=0.7, legend='Combined equity curve SMA({})'.format(self._EQUITY_CURVE_SMA1_LENGTH))

        if self.is_possible_to_draw_sma(combined_x_data, self._EQUITY_CURVE_SMA2_LENGTH):
            equity_curve_sma2_y_data = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA2_LENGTH, combined_y_data)
            equity_curve_plot.line(combined_x_data, equity_curve_sma2_y_data, color='magenta', line_width=1, alpha=0.5, legend='Combined equity curve SMA({})'.format(self._EQUITY_CURVE_SMA2_LENGTH))

        equity_curve_plot.legend.location = "bottom_right"

        return column(description, equity_curve_plot)

    def generate_equity_curve_images(self, results_df, equity_curve_df, args):
        image_counter = 0
        base_dir = self.whereAmI()
        output_path = self.get_output_equity_curve_images_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)
        print("Rendering {} equity curve images into {}".format(len(results_df), output_path))
        for index, row in results_df.iterrows():
            strategy_str = row['Strategy ID']
            exchange_str = row['Exchange']
            symbol_str = row['Currency Pair']
            timeframe_str = row['Timeframe']
            parameters_str = row['Parameters']
            equitycurveslope = round(row['Equity Curve Slope'], 3)
            equitycurveintercept = round(row['Equity Curve Intercept'], 3)
            equity_curve_data_points_str = self.get_equity_curve_data_points(equity_curve_df, strategy_str, exchange_str, symbol_str, timeframe_str, parameters_str)
            draw_column = self.draw_equity_curve(row, equity_curve_data_points_str, equitycurveslope, equitycurveintercept)
            image_counter += 1
            if image_counter % 10 == 0:
                print("Rendered {} equity curve images...".format(image_counter))
            image_filename = self.get_output_image_filename(output_path, strategy_str, exchange_str, symbol_str, timeframe_str, image_counter)
            export_png(draw_column, filename=image_filename)

    def generate_combined_equity_curves_images(self, results_df, bktest_equity_curve_df, fwtest_equity_curve_df, args):
        image_counter = 0
        base_dir = self.whereAmI()
        output_path = self.get_output_equity_curve_images_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)
        print("Rendering {} equity curves images into {}".format(len(results_df), output_path))
        for index, row in results_df.iterrows():
            strategy_str = row['Strategy ID']
            exchange_str = row['Exchange']
            symbol_str = row['Currency Pair']
            timeframe_str = row['Timeframe']
            parameters_str = row['Parameters']
            bktest_equity_curve_data_points_str = self.get_equity_curve_data_points(bktest_equity_curve_df, strategy_str, exchange_str, symbol_str, timeframe_str, parameters_str)
            fwtest_equity_curve_data_points_str = self.get_equity_curve_data_points(fwtest_equity_curve_df, strategy_str, exchange_str, symbol_str, timeframe_str, parameters_str)
            draw_column = self.draw_combined_equity_curves(row, bktest_equity_curve_data_points_str, fwtest_equity_curve_data_points_str)
            image_counter += 1
            if image_counter % 10 == 0:
                print("Rendered {} equity curve images...".format(image_counter))
            image_filename = self.get_output_image_filename(output_path, strategy_str, exchange_str, symbol_str, timeframe_str, image_counter)
            export_png(draw_column, filename=image_filename)