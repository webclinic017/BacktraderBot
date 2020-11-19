class BacktestRunKey(object):

    def __init__(self):
        self.strategyid    = None
        self.exchange      = None
        self.currency_pair = None
        self.timeframe     = None
        self.parameters    = None
        self.wfo_cycle     = None


class BacktestAnalyzerData(object):
    def __init__(self):
        self.daterange = None
        self.startcash = None
        self.lot_size = None
        self.processing_status = None
        self.total_closed_trades = None
        self.sl_trades_count = None
        self.tsl_trades_count = None
        self.tsl_moved_count = None
        self.tp_trades_count = None
        self.ttp_trades_count = None
        self.ttp_moved_count = None
        self.tb_trades_count = None
        self.tb_moved_count = None
        self.dca_triggered_count = None
        self.net_profit = None
        self.net_profit_pct = None
        self.avg_monthly_net_profit_pct = None
        self.max_drawdown_pct = None
        self.max_drawdown_length = None
        self.net_profit_to_maxdd = None
        self.win_rate_pct = None
        self.trades_len_avg = None
        self.trade_bars_ratio_pct = None
        self.num_winning_months = None
        self.profit_factor = None
        self.buy_and_hold_return_pct = None
        self.sqn_number = None
        self.monthlystatsprefix = None
        self.monthly_stats = None


class BacktestEquityCurveData(object):
    def __init__(self):
        self.equitycurvedata = None
        self.equitycurveangle = None
        self.equitycurveslope = None
        self.equitycurveintercept = None
        self.equitycurvervalue = None
        self.equitycurversquaredvalue = None
        self.equitycurvepvalue = None
        self.equitycurvestderr = None


class BacktestMonteCarloData(object):
    def __init__(self):
        self.mc_riskofruin_pct = None
        self.mc_mediandd_pct = None
        self.mc_medianreturn_pct = None
