class LinearRegressionStats(object):
    angle = None
    slope = None
    intercept = None
    r_value = None
    p_value = None
    std_err = None
    r_squared = None

    def __init__(self, angle, slope, intercept, r_value, r_squared, p_value, std_err):
        self.angle = angle
        self.slope = slope
        self.intercept = intercept
        self.r_value = r_value
        self.r_squared = r_squared
        self.p_value = p_value
        self.std_err = std_err


class WFOMode(object):
    WFO_MODE_NONE = 1
    WFO_MODE_TRAINING = 2
    WFO_MODE_TESTING = 3

    def __init__(self):
        pass


class StrategyRunData(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe):
        self.strategyid     = strategyid
        self.exchange       = exchange
        self.currency_pair  = currency_pair
        self.timeframe      = timeframe


class StrategyConfig(object):
    def __init__(self):
        self.lotsize = None
        self.lottype = None


class BacktestRunKey(object):
    def __init__(self):
        self.strategyid            = None
        self.exchange              = None
        self.currency_pair         = None
        self.timeframe             = None
        self.parameters            = None
        self.wfo_cycle_id          = None
        self.wfo_cycle_training_id = None


class BacktestAnalyzerData(object):
    def __init__(self):
        self.wfo_training_period = None
        self.wfo_testing_period = None
        self.trainingdaterange = None
        self.testingdaterange = None
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
        self.monthly_stats = None


class EquityCurveData(object):
    def __init__(self):
        self.equitycurvedata = None
        self.equitycurveangle = None
        self.equitycurveslope = None
        self.equitycurveintercept = None
        self.equitycurvervalue = None
        self.equitycurversquaredvalue = None
        self.equitycurvepvalue = None
        self.equitycurvestderr = None


class MonteCarloData(object):
    def __init__(self):
        self.mc_riskofruin_pct = None
        self.mc_mediandd_pct = None
        self.mc_medianreturn_pct = None


class WFOCycleInfo(object):
    def __init__(self, wfo_cycle_id, wfo_training_period, wfo_testing_period, training_start_date, training_end_date, testing_start_date, testing_end_date):
        self.wfo_cycle_id = wfo_cycle_id
        self.wfo_training_period = wfo_training_period
        self.wfo_testing_period = wfo_testing_period
        self.training_start_date = training_start_date
        self.training_end_date = training_end_date
        self.testing_start_date = testing_start_date
        self.testing_end_date = testing_end_date


class WFOTestingData(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe):
        self.strategyid     = strategyid
        self.exchange       = exchange
        self.currency_pair  = currency_pair
        self.timeframe      = timeframe
        self.wfo_cycles_dict     = dict()   # dict:  WFO Cycle Id -> WFOCycleInfo
        self.trained_params_dict = dict()   # dict:  WFO Cycle Training Id -> Dict: WFO Cycle Id -> Trained Parameters

    def set_wfo_cycle(self, wfo_cycle_info):
        self.wfo_cycles_dict[wfo_cycle_info.wfo_cycle_id] = wfo_cycle_info

    def get_num_wfo_cycles(self):
        return len(self.wfo_cycles_dict.keys())

    def get_num_trained_params(self):
        return len(self.trained_params_dict.keys())
