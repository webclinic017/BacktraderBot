from .common import BacktestRunKey
from .common import BacktestAnalyzerData
from .common import BacktestEquityCurveData
from .common import BacktestMonteCarloData


class BacktestModelGenerator(object):

    def __init__(self, needfiltering):
        self._needfiltering = needfiltering

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def update_monthly_stats(self, stats, num_months):
        if len(stats) > 0:
            # Workaround: delete the last element of stats array - do not need to see last month of the whole calculation
            if len(stats) == num_months + 1:
                stats.popitem()

        return stats

    def getparametersstr(self, params):
        coll = vars(params).copy()
        del coll["debug"]
        del coll["startcash"]
        del coll["fromyear"]
        del coll["frommonth"]
        del coll["fromday"]
        del coll["toyear"]
        del coll["tomonth"]
        del coll["today"]
        return "{}".format(coll)

    def get_avg_monthly_net_profit_pct(self, monthly_stats, num_months):
        sum_netprofits = 0
        for key, val in monthly_stats.items():
            curr_netprofit = val.pnl.netprofit.pct
            sum_netprofits += curr_netprofit
        return round(sum_netprofits / float(num_months) if num_months > 0 else 0, 2)

    def get_num_winning_months(self, monthly_stats, num_months):
        num_positive_netprofit_months = 0
        for key, val in monthly_stats.items():
            curr_netprofit = val.pnl.netprofit.total
            if curr_netprofit > 0:
                num_positive_netprofit_months += 1
        return round(num_positive_netprofit_months * 100 / float(num_months) if num_months > 0 else 0, 2)

    def getlotsize(self, lotsize, lottype):
        return "Lot{}{}".format(lotsize, "Pct" if lottype == "Percentage" else "")

    def get_pct_fmt(self, val):
        return "{}%".format(round(val, 2))

    def populate_model_data(self, wfo_cycle, model, backtest_run_results, strategy_id, exchange, symbol, timeframe, args, lotsize, lottype, proc_daterange):
        # Generate backtesting model data
        for run in backtest_run_results:
            for strategy in run:
                # print the analyzers
                ta_analysis = strategy.analyzers.ta.get_analysis()
                sqn_analysis = strategy.analyzers.sqn.get_analysis()
                dd_analysis = strategy.analyzers.dd.get_analysis()

                run_key = BacktestRunKey()
                run_key.strategyid = strategy_id
                run_key.exchange = exchange
                run_key.currency_pair = symbol
                run_key.timeframe = timeframe
                run_key.parameters = self.getparametersstr(strategy.params)
                run_key.wfo_cycle = wfo_cycle

                analyzer_data = BacktestAnalyzerData()
                analyzer_data.daterange = proc_daterange
                analyzer_data.startcash = strategy.params.startcash
                analyzer_data.lot_size = self.getlotsize(lotsize, lottype)
                analyzer_data.processing_status = ta_analysis.processing_status if self.exists(ta_analysis, ['processing_status']) else "N/A"
                analyzer_data.total_closed_trades = ta_analysis.total.closed if self.exists(ta_analysis, ['total', 'closed']) else 0
                analyzer_data.sl_trades_count = ta_analysis.sl.count if self.exists(ta_analysis, ['sl', 'count']) else 0
                analyzer_data.tsl_trades_count = ta_analysis.tsl.count if self.exists(ta_analysis, ['tsl', 'count']) else 0
                analyzer_data.tsl_moved_count = ta_analysis.tsl.moved.count if self.exists(ta_analysis, ['tsl', 'moved', 'count']) else 0
                analyzer_data.tp_trades_count = ta_analysis.tp.count if self.exists(ta_analysis, ['tp', 'count']) else 0
                analyzer_data.ttp_trades_count = ta_analysis.ttp.count if self.exists(ta_analysis, ['ttp', 'count']) else 0
                analyzer_data.ttp_moved_count = ta_analysis.ttp.moved.count if self.exists(ta_analysis, ['ttp', 'moved', 'count']) else 0
                analyzer_data.tb_trades_count = ta_analysis.tb.count if self.exists(ta_analysis, ['tb', 'count']) else 0
                analyzer_data.tb_moved_count = ta_analysis.tb.moved.count if self.exists(ta_analysis, ['tb', 'moved', 'count']) else 0
                analyzer_data.dca_triggered_count = ta_analysis.dca.triggered.count if self.exists(ta_analysis, ['dca', 'triggered', 'count']) else 0
                analyzer_data.net_profit = round(ta_analysis.pnl.netprofit.total, 8) if self.exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                analyzer_data.net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total / strategy.params.startcash, 2) if self.exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                monthly_stats = ta_analysis.monthly_stats if self.exists(ta_analysis, ['monthly_stats']) else {}
                num_months = model.get_num_months()
                monthly_stats = self.update_monthly_stats(monthly_stats, num_months)
                analyzer_data.monthly_stats = monthly_stats
                analyzer_data.avg_monthly_net_profit_pct = '{}%'.format(self.get_avg_monthly_net_profit_pct(monthly_stats, num_months))
                analyzer_data.max_drawdown_pct = round(dd_analysis.max.drawdown, 2)
                analyzer_data.max_drawdown_length = round(dd_analysis.max.len)
                analyzer_data.net_profit_to_maxdd = round(abs(analyzer_data.net_profit_pct / dd_analysis.max.drawdown), 2) if analyzer_data.max_drawdown_pct != 0 else 0
                total_won = ta_analysis.won.total if self.exists(ta_analysis, ['won', 'total']) else 0
                analyzer_data.win_rate_pct = '{}%'.format(round((total_won / analyzer_data.total_closed_trades) * 100, 2)) if analyzer_data.total_closed_trades > 0 else "0.0%"
                analyzer_data.trades_len_avg = round(ta_analysis.len.average) if self.exists(ta_analysis, ['len', 'average']) else 0
                analyzer_data.trade_bars_ratio_pct = '{}%'.format(round(ta_analysis.len.tradebarsratio_pct, 2)) if self.exists(ta_analysis, ['len', 'tradebarsratio_pct']) else "0.0%"
                analyzer_data.num_winning_months = '{}'.format(self.get_num_winning_months(monthly_stats, num_months))
                analyzer_data.profit_factor = round(ta_analysis.total.profitfactor, 3) if self.exists(ta_analysis, ['total', 'profitfactor']) else 0
                analyzer_data.buy_and_hold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if self.exists(ta_analysis, ['total', 'buyandholdreturnpct']) else 0
                analyzer_data.sqn_number = round(sqn_analysis.sqn, 2)
                analyzer_data.monthlystatsprefix = args.monthlystatsprefix if "monthlystatsprefix" in args else ""

                equity_curve_data = BacktestEquityCurveData()
                equity_curve_data.equitycurvedata = ta_analysis.total.equity.equitycurvedata if self.exists(ta_analysis, ['total', 'equity', 'equitycurvedata']) else {}
                equity_curve_data.equitycurveangle = round(ta_analysis.total.equity.stats.angle) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'angle']) else 0
                equity_curve_data.equitycurveslope = round(ta_analysis.total.equity.stats.slope, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'slope']) else 0
                equity_curve_data.equitycurveintercept = round(ta_analysis.total.equity.stats.intercept, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'intercept']) else 0
                equity_curve_data.equitycurvervalue = round(ta_analysis.total.equity.stats.r_value, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'r_value']) else 0
                equity_curve_data.equitycurversquaredvalue = round(ta_analysis.total.equity.stats.r_squared, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'r_squared']) else 0
                equity_curve_data.equitycurvepvalue = round(ta_analysis.total.equity.stats.p_value, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'p_value']) else 0
                equity_curve_data.equitycurvestderr = round(ta_analysis.total.equity.stats.std_err, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'std_err']) else 0

                montecarlo_data = BacktestMonteCarloData()
                montecarlo_data.mc_riskofruin_pct =   self.get_pct_fmt(100 * ta_analysis.total.mcsimulation.risk_of_ruin) if self.exists(ta_analysis, ['total', 'mcsimulation', 'risk_of_ruin']) else "0.0%"
                montecarlo_data.mc_mediandd_pct =     self.get_pct_fmt(100 * ta_analysis.total.mcsimulation.median_dd) if self.exists(ta_analysis, ['total', 'mcsimulation', 'median_dd']) else "0.0%"
                montecarlo_data.mc_medianreturn_pct = self.get_pct_fmt(100 * ta_analysis.total.mcsimulation.median_return) if self.exists(ta_analysis, ['total', 'mcsimulation', 'median_return']) else "0.0%"

                if self._needfiltering is False or self._needfiltering is True and analyzer_data.net_profit > 0 and analyzer_data.total_closed_trades > 0:
                    model.add_result_row(run_key, analyzer_data, equity_curve_data, montecarlo_data)

        return model
