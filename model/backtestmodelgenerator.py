

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
            curr_netprofit = val.pnl.netprofit.total
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

    def populate_model_data(self, model, backtest_run_results, strategy_id, exchange, symbol, timeframe, args, lotsize, lottype, proc_daterange):
        # Generate backtesting model data
        for run in backtest_run_results:
            for strategy in run:
                startcash = strategy.params.startcash
                # print the analyzers
                ta_analysis = strategy.analyzers.ta.get_analysis()
                sqn_analysis = strategy.analyzers.sqn.get_analysis()
                dd_analysis = strategy.analyzers.dd.get_analysis()

                parameters = self.getparametersstr(strategy.params)
                monthly_stats = ta_analysis.monthly_stats if self.exists(ta_analysis, ['monthly_stats']) else {}
                num_months = model.get_num_months()
                monthly_stats = self.update_monthly_stats(monthly_stats, num_months)
                total_closed = ta_analysis.total.closed if self.exists(ta_analysis, ['total', 'closed']) else 0
                net_profit = round(ta_analysis.pnl.netprofit.total, 8) if self.exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                net_profit_pct = round(100 * ta_analysis.pnl.netprofit.total / startcash, 2) if self.exists(ta_analysis, ['pnl', 'netprofit', 'total']) else 0
                avg_monthly_net_profit_pct = '{}%'.format(self.get_avg_monthly_net_profit_pct(monthly_stats, num_months))
                total_won = ta_analysis.won.total if self.exists(ta_analysis, ['won', 'total']) else 0
                strike_rate = '{}%'.format(round((total_won / total_closed) * 100, 2)) if total_closed > 0 else "0.0%"
                max_drawdown_pct = round(dd_analysis.max.drawdown, 2)
                max_drawdown_length = round(dd_analysis.max.len)
                net_profit_to_maxdd = round(abs(net_profit_pct / dd_analysis.max.drawdown), 2) if max_drawdown_pct != 0 else 0
                num_winning_months = '{}'.format(self.get_num_winning_months(monthly_stats, num_months))
                profitfactor = round(ta_analysis.total.profitfactor, 3) if self.exists(ta_analysis, ['total', 'profitfactor']) else 0
                buyandhold_return_pct = round(ta_analysis.total.buyandholdreturnpct, 2) if self.exists(ta_analysis, ['total', 'buyandholdreturnpct']) else 0
                sqn_number = round(sqn_analysis.sqn, 2)
                monthlystatsprefix = args.monthlystatsprefix if "monthlystatsprefix" in args else ""
                equitycurvedata = ta_analysis.total.equity.equitycurvedata if self.exists(ta_analysis, ['total', 'equity', 'equitycurvedata']) else {}
                equitycurveangle = round(ta_analysis.total.equity.stats.angle) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'angle']) else 0
                equitycurveslope = round(ta_analysis.total.equity.stats.slope, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'slope']) else 0
                equitycurveintercept = round(ta_analysis.total.equity.stats.intercept, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'intercept']) else 0
                equitycurvervalue = round(ta_analysis.total.equity.stats.r_value, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'r_value']) else 0
                equitycurvepvalue = round(ta_analysis.total.equity.stats.p_value, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'p_value']) else 0
                equitycurvestderr = round(ta_analysis.total.equity.stats.std_err, 3) if self.exists(ta_analysis, ['total', 'equity', 'stats', 'std_err']) else 0

                if self._needfiltering is False or self._needfiltering is True and net_profit > 0 and total_closed > 0:
                    model.add_result_row(strategy_id, exchange, symbol, timeframe, parameters, proc_daterange, startcash, self.getlotsize(lotsize, lottype),
                                         total_closed, net_profit, net_profit_pct, avg_monthly_net_profit_pct, max_drawdown_pct, max_drawdown_length, net_profit_to_maxdd, strike_rate,
                                         num_winning_months, profitfactor, buyandhold_return_pct, sqn_number, monthlystatsprefix, monthly_stats, equitycurvedata, equitycurveangle,
                                         equitycurveslope, equitycurveintercept, equitycurvervalue, equitycurvepvalue, equitycurvestderr)
