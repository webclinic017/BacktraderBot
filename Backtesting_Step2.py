'''
Step 2 of backtesting process
'''
 
import argparse
import os
import csv
import pandas as pd
from config.optimization import StrategyOptimizationFactory
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Span, Label
from bokeh.plotting import figure
from bokeh.io import export_png
from datetime import datetime
from bokeh.models import DatetimeTickFormatter
from bokeh.models import NumeralTickFormatter
import json


class BacktestingStep2(object):

    _EQUITY_CURVE_IMAGE_WIDTH = 1500
    _EQUITY_CURVE_IMAGE_HEIGHT = 800

    _INDEX_NUMBERS_ARR = [0, 1, 2, 3, 4]

    _SORT_FINAL_RESULTS_COLUMN_NAME = "Net Profit"

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
        return '{}/strategyrun_results/{}/{}_Step1_NetProfitsData.csv'.format(dirname, args.runid, args.runid)

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
        return "{}/{}-{}-{}-{}-{:04d}.png".format(base_path, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, image_counter)

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

    def do_filter_input_data(self, df):
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
                        candidates_data_df = self.filter_top_records(candidates_data_df)
                        if candidates_data_df is not None and len(candidates_data_df) > 0:
                            print("Processing: {}/{}/{}/{}:\nNumber of best rows: {}\n".format(strategy, exchange, symbol, timeframe, len(candidates_data_df.values)))
                            candidates_data_df = candidates_data_df.reset_index()
                            final_results.extend(candidates_data_df.values.tolist())
                            #print("candidates_data_df.values={}\n".format(candidates_data_df.values))

        print("==========================\nFinal number of rows: {}".format(len(final_results)))
        return final_results

    def sort_results(self, arr, header_names):
        sort_by_column_idx = header_names.index(self._SORT_FINAL_RESULTS_COLUMN_NAME)
        return sorted(arr, key=lambda x: x[sort_by_column_idx], reverse=True)

    def printfinalresults(self, writer, arr):
        print_list = []
        print_list.extend(arr)
        for item in print_list:
            writer.writerow(item)

    def get_equity_curve_dates(self, dates_arr, date_range_str):
        counter = 1
        range_splitted = date_range_str.split('-')
        start_date = range_splitted[0]
        result = [datetime.strptime(start_date, '%Y%m%d')]
        for eq_date_str in dates_arr:
            eq_date = datetime.strptime(eq_date_str, '%y%m%d')
            eq_date = pd.to_datetime(eq_date)
            result.append(eq_date)
            counter += 1
        return result

    def get_equity_curve_data(self, netprofit_data_arr):
        equity = 0
        result = [equity]
        for netprofit_val in netprofit_data_arr:
            equity += netprofit_val
            result.append(equity)
        return result

    def get_net_profits_data(self, step1_equity_curve_df, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str):
        net_profits_data = step1_equity_curve_df.loc[(strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str), "Net Profits Data"]
        return net_profits_data

    def draw_plot(self, date_range_str, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str, net_profits_data_str):
        labels = figure(tools="", toolbar_location=None, plot_height=150, plot_width=self._EQUITY_CURVE_IMAGE_WIDTH,
                        x_axis_location="above")
        label1 = Label(x=10, y=110, x_units='screen', y_units='screen', text=date_range_str, text_font_size="10pt",
                       render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)
        label2 = Label(x=10, y=90, x_units='screen', y_units='screen', text=strategy_id_data_str, text_font_size="10pt",
                       render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)
        label3 = Label(x=10, y=70, x_units='screen', y_units='screen', text=exchange_str, text_font_size="10pt",
                       render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)
        label4 = Label(x=10, y=50, x_units='screen', y_units='screen', text=symbol_str, text_font_size="10pt",
                       render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)
        label5 = Label(x=10, y=30, x_units='screen', y_units='screen', text=timeframe_str, text_font_size="10pt",
                       render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)
        label6 = Label(x=10, y=10, x_units='screen', y_units='screen', text=parameters_str, text_font_size="10pt",
                       render_mode='canvas', border_line_alpha=0, background_fill_alpha=0)
        labels.add_layout(label1)
        labels.add_layout(label2)
        labels.add_layout(label3)
        labels.add_layout(label4)
        labels.add_layout(label5)
        labels.add_layout(label6)

        net_profits_data_dict = json.loads(net_profits_data_str)
        x_axis_data = self.get_equity_curve_dates(net_profits_data_dict.keys(), date_range_str)
        y_axis_data = self.get_equity_curve_data(net_profits_data_dict.values())
        source = ColumnDataSource(data=dict(id=x_axis_data, netprofit=y_axis_data))
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
        y_axis_zero_line = Span(location=0, dimension='width', line_color='blue', line_dash='dashed', line_width=1, line_alpha=0.8)
        equity_curve_plot.add_layout(y_axis_zero_line)
        equity_curve_plot.line('id', 'netprofit', source=source, line_width=2, alpha=0.7)

        return column(labels, equity_curve_plot)

    def generate_equity_curve_images(self, step2_results, step1_equity_curve_df, args):
        image_counter = 0
        base_dir = self.whereAmI()
        output_path = self.get_output_equity_curve_images_path(base_dir, args)
        os.makedirs(output_path, exist_ok=True)
        for row in step2_results:
            date_range_str = row[5]
            strategy_id_data_str = row[0]
            exchange_str = row[1]
            symbol_str = row[2]
            timeframe_str = row[3]
            parameters_str = row[4]
            net_profits_data_str = self.get_net_profits_data(step1_equity_curve_df, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str)
            draw_column = self.draw_plot(date_range_str, strategy_id_data_str, exchange_str, symbol_str, timeframe_str, parameters_str, net_profits_data_str)

            image_counter += 1
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

        step2_results = self.do_filter_input_data(step1_df)

        print("Writing Step2 backtesting run results to: {}".format(self._output_file1_full_name))

        step2_results = self.sort_results(step2_results, header_names)

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