from model.step5model import Step5Model
import re

class Step5ModelGenerator(object):

    def __init__(self):
        pass

    def parse_pct_to_float(self, str_val):
        val = str_val.replace("%", "")
        return float(val)

    def parse_monthly_stats(self, df, columns):
        result = {}
        for column in columns:
            daterange_regex = "(\d{8}-\d{8})"
            month_range = re.search(daterange_regex, column)
            if month_range:
                month_value = df[column]
                net_profit_pct = re.match("[-+]?[0-9]*\.?[0-9]+", month_value)
                if net_profit_pct:
                    net_profit_pct = float(net_profit_pct.group())
                    month_key = month_range.group(1)
                    result[month_key] = net_profit_pct
        return result

    def generate_model(self, df, args):
        model = Step5Model()
        df = df.copy()
        df = df.reset_index()
        for index, row in df.iterrows():
            strategyid          = row['Strategy ID']
            exchange            = row['Exchange']
            currency_pair       = row['Currency Pair']
            timeframe           = row['Timeframe']
            parameters          = row['Parameters']
            startcash           = row['Start Cash']
            commission          = args.commission * 100
            leverage            = 1
            pyramiding          = 1
            profit_factor       = row['Profit Factor']
            win_rate_pct        = self.parse_pct_to_float(row['Win Rate, %'])
            max_drawdown_pct    = row['Max Drawdown, %']
            total_closed_trades = row['Total Closed Trades']
            monthly_stats = self.parse_monthly_stats(row, df.columns.values)
            model.add_result_column(strategyid, exchange, currency_pair, timeframe, parameters, startcash, commission, leverage, pyramiding, profit_factor, win_rate_pct, max_drawdown_pct, total_closed_trades, monthly_stats)
        return model