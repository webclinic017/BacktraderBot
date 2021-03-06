import backtrader as bt
import backtrader.feeds as btfeeds
from datetime import datetime
from datetime import timedelta
import argparse
from extensions.analyzers.drawdown import TVNetProfitDrawDown
from extensions.analyzers.tradeanalyzer import TVTradeAnalyzer
from extensions.sizers.percentsizer import VariablePercentSizer
from extensions.sizers.cashsizer import FixedCashSizer
from config.strategy_config import AppConfig
from config.strategy_enum import BTStrategyEnum
from plotting.equity_curve import EquityCurvePlotter
from model.backtestmodel import BacktestModel
from model.backtestmodelgenerator import BacktestModelGenerator
from strategies.helper.utils import Utils
from model.common import WFOMode
from wfo.wfo_helper import WFOHelper
from model.common import WFOMode, StrategyRunData, StrategyConfig
from model.reports_common import ColumnName
import pandas as pd

tradesopen = {}
tradesclosed = {}


class DebugStrategy(object):

    _INDEX_COLUMNS = [ColumnName.STRATEGY_ID, ColumnName.EXCHANGE, ColumnName.CURRENCY_PAIR, ColumnName.TIMEFRAME, ColumnName.PARAMETERS]

    def __init__(self):
        self._exchange = None
        self._currency_pair = None
        self._timeframe = None
        self._startcash = None
        self._lotsize = None
        self._lottype = None
        self._startyear = None
        self._startmonth = None
        self._startday = None
        self._num_wfo_cycles = None
        self._wfo_training_period = None
        self._wfo_testing_period = None

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

        parser.add_argument('--commission',
                            default=AppConfig.get_global_default_commission(),
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('--risk',
                            default=AppConfig.get_global_default_risk(),
                            type=float,
                            help='The percentage of capital to risk on a trade')

        parser.add_argument('--debug',
                            action ='store_true',
                            help=('Print Debug logs'))

        return parser.parse_args()

    def init_cerebro(self, args, startcash, lotsize, lottype):
        # Create an instance of cerebro
        self._cerebro = bt.Cerebro(cheat_on_open=True)

        # Set our desired cash start
        self._cerebro.broker.setcash(startcash)

        # Add the analyzers we are interested in
        self._cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self._cerebro.addanalyzer(TVNetProfitDrawDown, _name="dd", initial_cash=startcash)
        self._cerebro.addanalyzer(TVTradeAnalyzer, _name="ta", cash=startcash)

        # add the sizer
        if lottype != "" and lottype == "Percentage":
            self._cerebro.addsizer(VariablePercentSizer, percents=lotsize, debug=args.debug)
        else:
            self._cerebro.addsizer(FixedCashSizer, lotsize=lotsize, commission=args.commission, risk=args.risk)

        if args.commtype.lower() == 'percentage':
            self._cerebro.broker.setcommission(args.commission)

    def get_strategy_enum(self, args):
        return BTStrategyEnum.get_strategy_enum_by_str(args.strategy)

    def init_params(self, strategy_enum, args):
        debug_strategy_config = AppConfig.get_default_strategy_params(strategy_enum)
        base_params = debug_strategy_config[0]
        params_dict = debug_strategy_config[1]
        self._exchange = base_params["exchange"]
        self._currency_pair = base_params["currency_pair"]
        self._timeframe = base_params["timeframe"]
        self._startcash = base_params["startcash"]
        self._lotsize = base_params["lotsize"]
        self._lottype = base_params["lottype"]
        self._startyear = base_params["startyear"]
        self._startmonth = base_params["startmonth"]
        self._startday = base_params["startday"]
        self._num_wfo_cycles = base_params["num_wfo_cycles"]
        self._wfo_training_period = base_params["wfo_training_period"]
        self._wfo_testing_period = base_params["wfo_test_period"]

        self._params = params_dict.copy()
        self._params.update(
            {
                ("debug", args.debug),
            }
        )

    def update_wfo_params(self, wfo_cycle_info):
        training_start_date = wfo_cycle_info.training_start_date.date()
        training_end_date = wfo_cycle_info.training_end_date.date()
        self._params.update({("wfo_cycle_id", 1),
                             ("wfo_cycle_training_id", 1),
                             ("startcash", self._startcash),
                             ("fromyear", training_start_date.year),
                             ("toyear", training_end_date.year),
                             ("frommonth", training_start_date.month),
                             ("tomonth", training_end_date.month),
                             ("fromday", training_start_date.day),
                             ("today", training_end_date.day)
        })

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

    def add_datas(self, wfo_cycle_info):
        fromdate = wfo_cycle_info.training_start_date.date()
        todate = wfo_cycle_info.training_end_date.date()

        data_tf = self.build_data(fromdate, todate, self._timeframe)

        # Add the data to Cerebro
        self._cerebro.adddata(data_tf, "data_{}".format(self._timeframe))

    def build_data(self, fromdate, todate, timeframe):
        fromdate_back_delta = timedelta(days=50)  # Adjust from date to add more candle data from the past to strategy to prevent any calculation problems with indicators
        granularity = Utils.get_granularity_by_tf_str(timeframe)
        timeframe_id = granularity[0][0]
        compression = granularity[0][1]
        fromdate_back = fromdate - fromdate_back_delta
        todate_delta = timedelta(days=2)  # Adjust to date to add more candle data
        todate_beyond = todate + todate_delta

        marketdata_filename = self.get_marketdata_filename(self._exchange, self._currency_pair, timeframe)
        return btfeeds.GenericCSVData(
            dataname=marketdata_filename,
            fromdate=fromdate_back,
            todate=todate_beyond,
            timeframe=timeframe_id,
            compression=compression,
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
        self.printMCSimulationResults(strategy.analyzers.ta.get_analysis())
        self.printSQN(strategy.analyzers.sqn.get_analysis())
        self.printDrawDown(strategy.analyzers.dd.get_analysis())

        print('\nTotal # trades: {}'.format(len(tradesclosed.items())))
        # Get final portfolio Value
        analyzer = strategy.analyzers.ta.get_analysis()
        netprofit = round(analyzer.pnl.netprofit.total, 8) if self.exists(analyzer, ['pnl', 'netprofit', 'total']) else 0
        portvalue = netprofit + startcash
        pnl = portvalue - startcash
        pnlpct = 100 * (portvalue / startcash) - 100
        print('Final Portfolio Value: {}'.format(round(portvalue, 2)))
        print('P/L: {}'.format(round(pnl, 2)))
        print('P/L, %: {}%'.format(round(pnlpct, 2)))

        self.printStatus(strategy.analyzers.ta.get_analysis())

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def get_pct_fmt(self, val):
        return "{}%".format(round(val, 2))

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
        win_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
        buyandhold_return = round(analyzer.total.buyandholdreturn, 8) if self.exists(analyzer, ['total', 'buyandholdreturn']) else 0
        buyandhold_return_pct = round(analyzer.total.buyandholdreturnpct, 2) if self.exists(analyzer, ['total', 'buyandholdreturnpct']) else 0
        trades_len_avg = round(analyzer.len.average) if self.exists(analyzer, ['len', 'average']) else 0
        trades_len_won_avg = round(analyzer.len.won.average) if self.exists(analyzer, ['len', 'won', 'average']) else 0
        trades_len_lost_avg = round(analyzer.len.lost.average) if self.exists(analyzer, ['len', 'lost', 'average']) else 0
        trade_bars_ratio = '{}%'.format(round(analyzer.len.tradebarsratio_pct, 2)) if self.exists(analyzer, ['len', 'tradebarsratio_pct']) else 0

        sl_trades_count = analyzer.sl.count if self.exists(analyzer, ['sl', 'count']) else 0
        tsl_trades_count = analyzer.tsl.count if self.exists(analyzer, ['tsl', 'count']) else 0
        tsl_moved_count = analyzer.tsl.moved.count if self.exists(analyzer, ['tsl', 'moved', 'count']) else 0
        tp_trades_count = analyzer.tp.count if self.exists(analyzer, ['tp', 'count']) else 0
        ttp_trades_count = analyzer.ttp.count if self.exists(analyzer, ['ttp', 'count']) else 0
        ttp_moved_count = analyzer.ttp.moved.count if self.exists(analyzer, ['ttp', 'moved', 'count']) else 0
        tb_trades_count = analyzer.tb.count if self.exists(analyzer, ['tb', 'count']) else 0
        tb_moved_count = analyzer.tb.moved.count if self.exists(analyzer, ['tb', 'moved', 'count']) else 0
        dca_triggered_trades_count = analyzer.dca.triggered.count if self.exists(analyzer, ['dca', 'triggered', 'count']) else 0

        # Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Win Rate', 'Win Streak', 'Losing Streak', '']
        h3 = ['Buy & Hold Return', 'Buy & Hold Return, %', '', '']
        h4 = ['Net Profit', 'Gross Profit', 'Gross Loss', 'Profit Factor']
        h5 = ['Avg # Bars In Trades', 'Avg # Bars In Won Trades', 'Avg # Bars In Lost Trades', 'Bars In Trades Ratio, %']
        h6 = ['Trades #: SL Count', 'Trades #: TSL Count', 'TSL Moved Count', '']
        h7 = ['Trades #: TP Count', 'Trades #: TTP Count', 'TTP Moved Count', '']
        h8 = ['Trades #: TB Count', 'TB Moved Count', 'Trades #: DCA Triggered Count', '']
        r1 = [total_open, total_closed, total_won, total_lost]
        r2 = [win_rate, win_streak, lose_streak, '']
        r3 = [buyandhold_return, buyandhold_return_pct, '', '']
        r4 = [netprofit, grossprofit, grossloss, profitfactor]
        r5 = [trades_len_avg, trades_len_won_avg, trades_len_lost_avg, trade_bars_ratio]
        r6 = [sl_trades_count, tsl_trades_count, tsl_moved_count, '']
        r7 = [tp_trades_count, ttp_trades_count, ttp_moved_count, '']
        r8 = [tb_trades_count, tb_moved_count, dca_triggered_trades_count, '']

        # Print the rows
        print_list = [h1, r1, h2, r2, h3, r3, h4, r4, h5, r5, h6, r6, h7, r7, h8, r8]
        row_format = "{:<30}" * (len(h1) + 1)
        print("Backtesting Results:")
        for row in print_list:
            print(row_format.format('', *row))

    def printMCSimulationResults(self, analyzer):
        mc_riskofruin_pct = self.get_pct_fmt(100 * analyzer.total.mcsimulation.risk_of_ruin) if self.exists(analyzer, ['total', 'mcsimulation', 'risk_of_ruin']) else "0.0%"
        print('MC Risk Of Ruin, %: {}'.format(mc_riskofruin_pct))

    def printSQN(self, analyzer):
        sqn = round(analyzer.sqn, 2)
        print('SQN: {}'.format(sqn))

    def printDrawDown(self, analyzer):
        print('Max Drawdown: {}'.format(round(analyzer.max.moneydown, 2)))
        print('Max Drawdown, %: {}%'.format(round(analyzer.max.drawdown, 2)))
        print('Max Drawdown Length: {}'.format(round(analyzer.max.len, 2)))

    def printStatus(self, analyzer):
        print('\nProcessing Status: {}'.format(analyzer.processing_status))

    def printDict(self, dict):
        for keys, values in dict.items():
            print(keys)
            print(values)

    def create_model(self, wfo_cycles, curr_wfo_cycle_info, run_results, args):
        model = BacktestModel(WFOMode.WFO_MODE_TRAINING, wfo_cycles)
        generator = BacktestModelGenerator(False)
        strategy_run_data = StrategyRunData(args.strategy, self._exchange, self._currency_pair, self._timeframe)
        strategy_config = StrategyConfig()
        strategy_config.lotsize = self._lotsize
        strategy_config.lottype = self._lottype
        generator.populate_model_data(model, strategy_run_data, strategy_config, curr_wfo_cycle_info, run_results)
        return model

    def render_equity_curve_image(self, bktest_model, args):
        bktest_results = bktest_model.get_model_data_arr()
        bktest_results_df = pd.DataFrame(bktest_results, columns=bktest_model.get_header_names())
        equity_curve = bktest_model.get_equity_curve_report_data_arr()
        equity_curve_df = pd.DataFrame(equity_curve, columns=bktest_model.get_equity_curve_header_names())
        equity_curve_df = equity_curve_df.set_index(self._INDEX_COLUMNS)
        print("")
        self._equity_curve_plotter.generate_images_common(bktest_results_df, equity_curve_df, args)

    def run(self):
        args = self.parse_args()

        self._strategy_enum = self.get_strategy_enum(args)
        self.init_params(self._strategy_enum, args)

        start_date = datetime(self._startyear, self._startmonth, self._startday)
        wfo_cycles = WFOHelper.get_wfo_cycles(start_date, self._num_wfo_cycles, self._wfo_training_period, self._wfo_testing_period)
        curr_wfo_cycle_info = wfo_cycles[0]
        self.update_wfo_params(curr_wfo_cycle_info)

        self.init_cerebro(args, self._startcash, self._lotsize, self._lottype)

        self.add_strategy()

        self.add_datas(curr_wfo_cycle_info)

        # Run the strategy
        strategies = self._cerebro.run()
        executed_strat = strategies[0]

        self.print_all_results(executed_strat, self._startcash)

        bktest_model = self.create_model(wfo_cycles, curr_wfo_cycle_info, [strategies], args)
        self.render_equity_curve_image(bktest_model, args)


def main():
    strat = DebugStrategy()
    strat.run()


if __name__ == '__main__':
    main()

