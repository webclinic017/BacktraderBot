'''
Step 2 of backtesting process
'''
 
import argparse
import os
import csv
import pandas as pd
import numpy as np
from config.optimization import StrategyOptimizationFactory
from bokeh.layouts import column
from bokeh.models import Span, Label
from bokeh.plotting import figure
from bokeh.io import export_png
from datetime import datetime
from bokeh.models import DatetimeTickFormatter
from bokeh.models import NumeralTickFormatter
from datetime import timedelta
import json


class BacktestingStep2(object):

    _ENABLE_FILTERING = True

    _EQUITY_CURVE_IMAGE_WIDTH = 1500
    _EQUITY_CURVE_IMAGE_HEIGHT = 800
    _EQUITY_CURVE_SMA1_LENGTH = 20
    _EQUITY_CURVE_SMA2_LENGTH = 40

    _INDEX_NUMBERS_ARR = [0, 1, 2, 3, 4]

    _params = None
    _input_filename = None
    _equity_curve_input_filename = None
    _output_file1_full_name = None
    _ofile1 = None
    _writer1 = None
    _step2_model = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtesting Step 2')

        parser.add_argument('-r', '--runid',
                            type=str,
                            required=True,
                            help='Name of the output file(RunId****) from Step1')

        parser.add_argument('--debug',
                            action='store_true',
                            help=('Print Debugs'))

        return parser.parse_args()

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step1.csv'.format(dirname, args.runid, args.runid)

    def get_equity_curve_input_filename(self, args):
        dirname = self.whereAmI()
        return '{}/strategyrun_results/{}/{}_Step1_EquityCurveData.csv'.format(dirname, args.runid, args.runid)

    def read_csv_data(self, filename):
        return pd.read_csv(filename, index_col=self._INDEX_NUMBERS_ARR)

    def get_header_names(self, df):
        return list(df.index.names) + list(df.columns.values)

    def get_unique_index_values(self, df, name):
        return df.index.get_level_values(name).unique()

    def filter_top_records(self, df):
        filter = StrategyOptimizationFactory.create_filters()
        return filter.filter(df)

    def get_output_path(self, base_dir, args):
        return '{}/strategyrun_results/{}'.format(base_dir, args.runid)

    def get_output_equity_curve_images_path(self, base_dir, args):
        return '{}/strategyrun_results/{}/Step2_EquityCurveImages'.format(base_dir, args.runid)

    def get_output_filename(self, base_path, args):
        return '{}/{}_Step2.csv'.format(base_path, args.runid)

    def get_output_image_filename(self, base_path, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, image_counter):
        return "{}/{:04d}-{}-{}-{}-{}.png".format(base_path, image_counter, strategy_id_data_str, exchange_str, symbol_str, timeframe_str)

    def init_output_files(self, args):
        base_dir = self.whereAmI()
        output_path = self.get_output_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)

        self._output_file1_full_name = self.get_output_filename(output_path, args)

        self._ofile1 = open(self._output_file1_full_name, "w")
        self._writer1 = csv.writer(self._ofile1, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

    def printheader(self, writer, arr):
        # Print header
        print_list = [arr]
        for row in print_list:
            writer.writerow(row)

    def filter_input_data(self, df):
        final_results = []

        strat_list = self.get_unique_index_values(df, 'Strategy ID')
        exc_list = self.get_unique_index_values(df, 'Exchange')
        sym_list = self.get_unique_index_values(df, 'Currency Pair')
        tf_list = self.get_unique_index_values(df, 'Timeframe')

        for strategy in strat_list:
            for exchange in exc_list:
                for symbol in sym_list:
                    for timeframe in tf_list:
                        idx = pd.IndexSlice
                        candidates_data_df = df.loc[idx[strategy, exchange, symbol, timeframe, :], idx[:]]
                        if self._ENABLE_FILTERING is True:
                            candidates_data_df = self.filter_top_records(candidates_data_df)
                        if candidates_data_df is not None and len(candidates_data_df) > 0:
                            print("Processing: {}/{}/{}/{}:\nNumber of best rows: {}\n".format(strategy, exchange, symbol, timeframe, len(candidates_data_df.values)))
                            candidates_data_df = candidates_data_df.reset_index()
                            final_results.extend(candidates_data_df.values.tolist())
                            #print("candidates_data_df.values={}\n".format(candidates_data_df.values))

        print("==========================\nFinal number of rows: {}".format(len(final_results)))
        return final_results

    def sort_results(self, arr):
        return sorted(arr, key=lambda x: (x[0], x[1], x[2], x[3], x[4]), reverse=False)

    def printfinalresults(self, writer, arr):
        print_list = []
        print_list.extend(arr)
        for item in print_list:
            writer.writerow(item)

    def build_plot_label(self, y_coord, txt):
        return Label(x=10, y=y_coord, x_units='screen', y_units='screen', text=txt, text_font_size="10pt", render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)

    def build_y_axis_zero_line(self):
        return Span(location=0, dimension='width', line_color='blue', line_dash='dashed', line_width=1, line_alpha=0.8)

    def build_equity_curve_plot_figure(self):
        equity_curve_plot = figure(plot_height=self._EQUITY_CURVE_IMAGE_HEIGHT, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, tools="", x_axis_type="datetime",
                                   toolbar_location=None, x_axis_label="Trade Number", x_axis_location="below",
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

    def get_equity_curve_dates(self, dates_arr):
        counter = 1
        dates_arr = list(dates_arr)
        first_date = datetime.strptime(dates_arr[0], '%y%m%d%H%M')
        first_date = pd.to_datetime(first_date)
        start_date = first_date - timedelta(days=1)
        result = [start_date]
        for eq_date_str in dates_arr:
            eq_date = datetime.strptime(eq_date_str, '%y%m%d%H%M')
            eq_date = pd.to_datetime(eq_date)
            result.append(eq_date)
            counter += 1
        return result

    def get_equity_data(self, equity_data_arr):
        result = [0]
        result.extend(list(equity_data_arr))
        return result

    def get_equity_curve_data_points(self, step1_equity_curve_df, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str):
        equity_curve_data_points = step1_equity_curve_df.loc[(strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str), "Equity Curve Data Points"]
        return equity_curve_data_points

    def get_linear_regression_points(self, x_axis_data, equitycurveslope, equitycurveintercept):
        x1 = x_axis_data[0]
        y1 = equitycurveintercept
        xn = x_axis_data[-1]
        yn = equitycurveintercept + len(x_axis_data) * equitycurveslope
        return [[x1, xn], [y1, yn]]

    def get_equity_curve_sma_points(self, sma_length, equity_curve_y_axis_data):
        equity_curve_avg = [float('nan')] * (sma_length - 1)
        calc_avg_data = np.convolve(equity_curve_y_axis_data, np.ones((sma_length,)) / sma_length, mode='valid')
        equity_curve_avg.extend(calc_avg_data)
        return equity_curve_avg

    def draw_plot(self, row, equity_curve_data_points_str):
        strategy_id_data_str = row[0]
        exchange_str = row[1]
        symbol_str = row[2]
        timeframe_str = row[3]
        date_range_str = row[5]
        parameters_str = row[4]
        total_closed_trades = row[7]
        net_profit_pct = row[9]
        max_drawdown_pct = row[11]
        max_drawdown_length = row[12]
        win_rate_pct = row[13]
        winning_months_pct = row[14]
        profit_factor = row[15]
        sqn = row[17]
        equitycurveangle = row[18]
        equitycurveslope = round(row[19], 3)
        equitycurveintercept = round(row[20], 3)
        equitycurvervalue = round(row[21], 3)
        equitycurvepvalue = round(row[22], 3)
        equitycurvestderr = round(row[23], 3)
        labels = figure(tools="", toolbar_location=None, plot_height=150, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH, x_axis_location="above")
        text1 = "{}, {}, {}, {}, {}".format(strategy_id_data_str, exchange_str, symbol_str, timeframe_str, date_range_str)
        text2 = "Params: {}".format(parameters_str)
        text3 = "Total Closed Trades: {}, Net Profit,%: {}%, Max Drawdown,%: {}%, Max Drawdown Length: {}, Win Rate,%: {}".format(total_closed_trades, net_profit_pct, max_drawdown_pct, max_drawdown_length, win_rate_pct)
        text4 = "Winning Months,%: {}%, Profit Factor: {}, SQN: {}: {}".format(winning_months_pct, profit_factor, sqn)
        text5 = "Equity Curve Angle={}°, Equity Curve Slope={}, Equity Curve Intercept={}, Equity Curve R-value={}, Equity Curve P-value={}, Equity Curve Stderr={}".format(equitycurveangle, equitycurveslope, equitycurveintercept, equitycurvervalue, equitycurvepvalue, equitycurvestderr)

        labels.add_layout(self.build_plot_label(110, text1))
        labels.add_layout(self.build_plot_label(90, text2))
        labels.add_layout(self.build_plot_label(70, text3))
        labels.add_layout(self.build_plot_label(50, text4))
        labels.add_layout(self.build_plot_label(30, text5))
        labels.add_layout(self.build_plot_label(10, ""))

        equity_curve_data_points_dict = json.loads(equity_curve_data_points_str)
        x_axis_data = self.get_equity_curve_dates(equity_curve_data_points_dict.keys())
        y_axis_data = self.get_equity_data(equity_curve_data_points_dict.values())
        equity_curve_plot = self.build_equity_curve_plot_figure()
        equity_curve_plot.line(x_axis_data, y_axis_data, line_width=3, alpha=0.7, legend='Equity curve')

        lr_points = self.get_linear_regression_points(x_axis_data, equitycurveslope, equitycurveintercept)
        equity_curve_plot.line(lr_points[0], lr_points[1], line_width=1, line_color="red", alpha=0.5, legend='Linear regression')

        equity_curve_sma1 = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA1_LENGTH, y_axis_data)
        equity_curve_plot.line(x_axis_data, equity_curve_sma1, color='orange', line_width=1, alpha=0.7, legend='Equity curve SMA1({})'.format(self._EQUITY_CURVE_SMA1_LENGTH))
        equity_curve_sma2 = self.get_equity_curve_sma_points(self._EQUITY_CURVE_SMA2_LENGTH, y_axis_data)
        equity_curve_plot.line(x_axis_data, equity_curve_sma2, color='green', line_width=1, alpha=0.7, legend='Equity curve SMA2({})'.format(self._EQUITY_CURVE_SMA2_LENGTH))
        equity_curve_plot.legend.location = "bottom_right"

        return column(labels, equity_curve_plot)

    def generate_equity_curve_images(self, step2_results, step1_equity_curve_df, args):
        image_counter = 0
        base_dir = self.whereAmI()
        output_path = self.get_output_equity_curve_images_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)
        print("Rendering {} equity curve images into {}".format(len(step2_results), output_path))
        for row in step2_results:
            strategy_id_data_str = row[0]
            exchange_str = row[1]
            symbol_str = row[2]
            timeframe_str = row[3]
            parameters_str = row[4]
            equity_curve_data_points_str = self.get_equity_curve_data_points(step1_equity_curve_df, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str)
            draw_column = self.draw_plot(row, equity_curve_data_points_str)
            image_counter += 1
            if image_counter % 10 == 0:
                print("Rendered {} equity curve images...".format(image_counter))
            image_filename = self.get_output_image_filename(output_path, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, image_counter)
            export_png(draw_column, filename=image_filename)
            #show(draw_column)

    def cleanup(self):
        self._ofile1.close()

    def run(self):
        args = self.parse_args()

        self._input_filename = self.get_input_filename(args)

        step1_df = self.read_csv_data(self._input_filename)

        header_names = self.get_header_names(step1_df)

        step1_df = step1_df.sort_index()

        self.init_output_files(args)

        self.printheader(self._writer1, header_names)

        step2_results = self.filter_input_data(step1_df)

        print("Writing Step2 backtesting run results to: {}".format(self._output_file1_full_name))

        step2_results = self.sort_results(step2_results)

        self.printfinalresults(self._writer1, step2_results)

        self._equity_curve_input_filename = self.get_equity_curve_input_filename(args)

        step1_equity_curve_df = self.read_csv_data(self._equity_curve_input_filename)

        self.generate_equity_curve_images(step2_results, step1_equity_curve_df, args)

        self.cleanup()


def main():
    step = BacktestingStep2()
    step.run()


if __name__ == '__main__':
    main()