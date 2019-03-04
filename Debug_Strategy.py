import backtrader as bt
import backtrader.feeds as btfeeds
from datetime import datetime
from datetime import timedelta
import argparse
from backtrader import TimeFrame
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from extensions.sizers.cashsizer import FixedCashSizer
from config.strategy_config import AppConfig
from config.strategy_enum import BTStrategyEnum
from plotting.equity_curve import EquityCurvePlotter
from model.backtestmodel import BacktestModel
from model.backtestmodelgenerator import BacktestModelGenerator
import pandas as pd

tradesopen = {}
tradesclosed = {}


class DebugStrategy(object):

    _INDEX_COLUMNS = ['Strategy ID', 'Exchange', 'Currency Pair', 'Timeframe', 'Parameters']

    def __init__(self):
        self._exchange = None
        self._currency_pair = None
        self._timeframe = None
        self._startcash = None
        self._lotsize = None
        self._cerebro = None
        self._strategy_enum = None
        self._params = None
        self._equity_curve_plotter = EquityCurvePlotter("Debug")

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Debug Strategy')

        parser.add_argument('-r', '--runid',
                            type=str,
                            default="TTTDebug",
                            help='Run ID')

        parser.add_argument('-y', '--strategy',
                            type=str,
                            required=True,
                            help='The strategy ID')

        parser.add_argument('--commtype',
                            default="Percentage",
                            type=str,
                            choices=["Percentage", "Fixed"],
                            help='The type of commission to apply to a trade')

        parser.add_argument('-l', '--lottype',
                            type=str,
                            default="Fixed",
                            choices=["Percentage", "Fixed"],
                            help='Lot type')

        parser.add_argument('--commission',
                            default=0.0015,
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('--risk',
                            default=0.02,
                            type=float,
                            help='The percentage of available cash to risk on a trade')

        parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Debug logs'))

        return parser.parse_args()

    def init_cerebro(self, args, startcash, lotsize):
        # Create an instance of cerebro
        self._cerebro = bt.Cerebro(cheat_on_open=True)

        # Set our desired cash start
        self._cerebro.broker.setcash(startcash)

        # Add the analyzers we are interested in
        self._cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self._cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd", initial_cash=startcash)
        self._cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=startcash)

        # add the sizer
        if args.lottype != "" and args.lottype == "Percentage":
            self._cerebro.addsizer(VariablePercentSizer, percents=lotsize, debug=args.debug)
        else:
            self._cerebro.addsizer(FixedCashSizer, cashamount=lotsize, commission=args.commission)

        if args.commtype.lower() == 'percentage':
            self._cerebro.broker.setcommission(args.commission)

    def get_strategy_enum(self, args):
        return BTStrategyEnum.get_strategy_enum_by_str(args.strategy)

    def init_params(self, strategy_enum, args):
        debug_strategy_config = AppConfig.get_debug_strategy_params(strategy_enum)
        base_params = debug_strategy_config[0]
        params_dict = debug_strategy_config[1]
        self._exchange = base_params["exchange"]
        self._currency_pair = base_params["currency_pair"]
        self._timeframe = base_params["timeframe"]
        self._startcash = base_params["startcash"]
        self._lotsize = base_params["lotsize"]
        self._params = params_dict.copy()
        self._params.update({("debug", args.debug)})

    def get_marketdata_filename(self, exchange, symbol, timeframe):
        return './marketdata/{}/{}/{}/{}-{}-{}.csv'.format(exchange, symbol, timeframe, exchange, symbol, timeframe)

    def add_strategy(self):
        strategy_class = self._strategy_enum.value.clazz
        self._cerebro.addstrategy(strategy_class, **self._params)

    def get_fromdate(self, arr):
        fromyear = arr["fromyear"]
        frommonth = arr["frommonth"]
        fromday = arr["fromday"]
        return datetime(fromyear, frommonth, fromday)

    def get_todate(self, arr):
        toyear = arr["toyear"]
        tomonth = arr["tomonth"]
        today = arr["today"]
        return datetime(toyear, tomonth, today)

    def add_data(self):
        fromdate = self.get_fromdate(self._params)
        todate = self.get_todate(self._params)

        fromdate_back_delta = timedelta(days=50)  # Adjust from date to add more candle data from the past to strategy to prevent any calculation problems with indicators
        fromdate_back = fromdate - fromdate_back_delta
        todate_delta = timedelta(days=2)  # Adjust to date to add more candle data
        todate_beyond = todate + todate_delta

        marketdata_filename = self.get_marketdata_filename(self._exchange, self._currency_pair, self._timeframe)
        data = btfeeds.GenericCSVData(
            dataname=marketdata_filename,
            fromdate=fromdate_back,
            todate=todate_beyond,
            timeframe=TimeFrame.Ticks,
            # compression=15,
            dtformat="%Y-%m-%dT%H:%M:%S",
            # nullvalue=0.0,
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            openinterest=-1
        )

        # Add the data to Cerebro
        self._cerebro.adddata(data)

    def print_all_results(self, strategy, startcash):
        # Print out the final result
        print('\n')
        for k, t in tradesclosed.items():
            opentrade = tradesopen[k]
            side = 'Long' if opentrade.size > 0 else 'Short'
            print('Trade Ref: {}'.format(t.ref))
            print('Trade Price: {}'.format(t.price))
            print('Trade Side: {}'.format(side))
            print('Trade dtopen: {}'.format(bt.num2date(t.dtopen)))
            print('Trade dtclose: {}'.format(bt.num2date(t.dtclose)))
            print('Trade barlen: {}'.format(t.barlen))
            print('Trade Profit NET: {}'.format(t.pnlcomm))
            print('Trade Profit GROSS: {}\n'.format(t.pnl))

        # print the analyzers
        self.printTradeAnalysis(strategy.analyzers.ta.get_analysis())
        self.printSQN(strategy.analyzers.sqn.get_analysis())
        self.printDrawDown(strategy.analyzers.dd.get_analysis())

        print('\nTotal # trades: {}'.format(len(tradesclosed.items())))
        # Get final portfolio Value
        portvalue = self._cerebro.broker.getvalue()
        pnl = portvalue - startcash
        pnlpct = 100 * (portvalue / startcash) - 100
        print('Final Portfolio Value: {}'.format(round(portvalue, 2)))
        print('P/L: {}'.format(round(pnl, 2)))
        print('P/L, %: {}%'.format(round(pnlpct, 2)))

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def get_equity_curve_data(self, netprofit_data_arr):
        equity = 0
        result = [equity]
        for netprofit_val in netprofit_data_arr:
            equity += netprofit_val
            result.append(equity)
        return result

    def printTradeAnalysis(self, analyzer):
        '''
        Function to print the Technical Analysis results in a nice format.
        '''
        # Get the results we are interested in
        total_open = analyzer.total.open if self.exists(analyzer, ['total', 'open']) else 0
        total_closed = analyzer.total.closed if self.exists(analyzer, ['total', 'closed']) else 0
        total_won = analyzer.won.total if self.exists(analyzer, ['won', 'total']) else 0
        total_lost = analyzer.lost.total if self.exists(analyzer, ['lost', 'total']) else 0
        win_streak = analyzer.streak.won.longest if self.exists(analyzer, ['streak', 'won', 'longest']) else 0
        lose_streak = analyzer.streak.lost.longest if self.exists(analyzer, ['streak', 'lost', 'longest']) else 0

        netprofit = round(analyzer.pnl.netprofit.total, 8) if self.exists(analyzer, ['pnl', 'netprofit', 'total']) else 0
        grossprofit = round(analyzer.pnl.grossprofit.total, 8) if self.exists(analyzer, ['pnl', 'grossprofit', 'total']) else 0
        grossloss = round(analyzer.pnl.grossloss.total, 8) if self.exists(analyzer, ['pnl', 'grossloss', 'total']) else 0
        profitfactor = round(analyzer.total.profitfactor, 3) if self.exists(analyzer, ['total', 'profitfactor']) else 0
        strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
        buyandhold_return = round(analyzer.total.buyandholdreturn, 8) if self.exists(analyzer, ['total', 'buyandholdreturn']) else 0
        buyandhold_return_pct = round(analyzer.total.buyandholdreturnpct, 2) if self.exists(analyzer, ['total', 'buyandholdreturnpct']) else 0
        equitycurvedata = analyzer.total.equity.equitycurvedata
        #print("equitycurvedata={}".format(equitycurvedata))

        #print("analyzer.total.equity.stats.angle = {}".format(analyzer.total.equity.stats.angle))
        #print("analyzer.total.equity.stats.slope = {}".format(analyzer.total.equity.stats.slope))
        #print("analyzer.total.equity.stats.intercept = {}".format(analyzer.total.equity.stats.intercept))
        #print("analyzer.total.equity.stats.r_value = {}".format(analyzer.total.equity.stats.r_value))
        #print("analyzer.total.equity.stats.p_value = {}".format(analyzer.total.equity.stats.p_value))
        #print("analyzer.total.equity.stats.std_err = {}".format(analyzer.total.equity.stats.std_err))

        # Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Win Rate', 'Win Streak', 'Losing Streak', '']
        h3 = ['Buy & Hold Return', 'Buy & Hold Return, %', '', '']
        h4 = ['Net Profit', 'Gross Profit', 'Gross Loss', 'Profit Factor']
        r1 = [total_open, total_closed, total_won, total_lost]
        r2 = [strike_rate, win_streak, lose_streak, '']
        r3 = [buyandhold_return, buyandhold_return_pct, '', '']
        r4 = [netprofit, grossprofit, grossloss, profitfactor]

        # Print the rows
        print_list = [h1, r1, h2, r2, h3, r3, h4, r4]
        row_format = "{:<25}" * (len(h1) + 1)
        print("Backtesting Results:")
        for row in print_list:
            print(row_format.format('', *row))

    def printSQN(self, analyzer):
        sqn = round(analyzer.sqn, 2)
        print('SQN: {}'.format(sqn))

    def printDrawDown(self, analyzer):
        print('Max Drawdown: {}'.format(round(analyzer.max.moneydown, 2)))
        print('Max Drawdown, %: {}%'.format(round(analyzer.max.drawdown, 2)))
        print('Max Drawdown Length: {}'.format(round(analyzer.max.len, 2)))

    def printDict(self, dict):
        for keys, values in dict.items():
            print(keys)
            print(values)

    def getdaterange(self, arr):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(arr["fromyear"], arr["frommonth"], arr["fromday"], arr["toyear"], arr["tomonth"], arr["today"])

    def create_model(self, run_results, args):
        debug_params = self._params
        model = BacktestModel(debug_params["fromyear"], debug_params["frommonth"], debug_params["toyear"], debug_params["tomonth"])
        generator = BacktestModelGenerator(False)
        generator.populate_model_data(model, run_results, args.strategy, self._exchange, self._currency_pair, self._timeframe, args, self.getdaterange(debug_params))
        return model

    def render_equity_curve_image(self, strategies, args):
        bktest_model = self.create_model([strategies], args)
        bktest_results = bktest_model.get_model_data_arr()
        bktest_results_df = pd.DataFrame(bktest_results, columns=bktest_model.get_header_names())
        equity_curve = bktest_model.get_equitycurvedata_model().get_model_data_arr()
        equity_curve_df = pd.DataFrame(equity_curve, columns=bktest_model.get_equitycurvedata_model().get_header_names())
        equity_curve_df = equity_curve_df.set_index(self._INDEX_COLUMNS)
        print("")
        self._equity_curve_plotter.generate_images(bktest_results_df, equity_curve_df, args)

    def run(self):
        args = self.parse_args()

        self._strategy_enum = self.get_strategy_enum(args)
        self.init_params(self._strategy_enum, args)

        startcash = self._startcash
        lotsize = self._lotsize

        self.init_cerebro(args, startcash, lotsize)

        self.add_strategy()

        self.add_data()

        # Run the strategy
        strategies = self._cerebro.run()
        executed_strat = strategies[0]

        self.print_all_results(executed_strat, startcash)

        self.render_equity_curve_image(strategies, args)


def main():
    strat = DebugStrategy()
    strat.run()


if __name__ == '__main__':
    main()

