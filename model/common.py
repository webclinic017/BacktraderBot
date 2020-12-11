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
        self.num_wfo_cycles = None
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
        self.data = None
        self.angle = None
        self.slope = None
        self.intercept = None
        self.rvalue = None
        self.rsquaredvalue = None
        self.pvalue = None
        self.stderr = None


class MonteCarloData(object):
    def __init__(self):
        self.mc_riskofruin_pct = None
        self.mc_mediandd_pct = None
        self.mc_medianreturn_pct = None


class WFOCycleInfo(object):
    def __init__(self, wfo_cycle_id, wfo_training_period, wfo_testing_period, training_start_date, training_end_date, testing_start_date, testing_end_date, num_wfo_cycles):
        self.wfo_cycle_id = wfo_cycle_id
        self.wfo_training_period = wfo_training_period
        self.wfo_testing_period = wfo_testing_period
        self.training_start_date = training_start_date
        self.training_end_date = training_end_date
        self.testing_start_date = testing_start_date
        self.testing_end_date = testing_end_date
        self.num_wfo_cycles = num_wfo_cycles


class WFOTestingData(object):
    def __init__(self, strategyid, exchange, currency_pair, timeframe):
        self.strategyid     = strategyid
        self.exchange       = exchange
        self.currency_pair  = currency_pair
        self.timeframe      = timeframe
        self.wfo_cycles_dict         = dict()   # dict:  WFO Cycle Id -> WFOCycleInfo
        self.training_id_params_dict = dict()   # dict:  WFO Cycle Training Id -> Dict: WFO Cycle Id -> Trained Parameters

    def get_wfo_cycles_list(self):
        return list(self.wfo_cycles_dict.values())

    def set_wfo_cycle(self, wfo_cycle_info):
        self.wfo_cycles_dict[wfo_cycle_info.wfo_cycle_id] = wfo_cycle_info

    def get_num_wfo_cycles(self):
        return len(self.wfo_cycles_dict.keys())

    def get_num_training_ids(self):
        return len(self.training_id_params_dict.keys())

    def getdaterange(self, date1, date2):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(date1.year, date1.month, date1.day, date2.year, date2.month, date2.day)

    def get_total_training_daterange_str(self):
        wfo_cycles_list = list(self.wfo_cycles_dict.values())
        first_cycle = wfo_cycles_list[0]
        last_cycle = wfo_cycles_list[-1]
        return self.getdaterange(first_cycle.training_start_date, last_cycle.training_end_date)

    def get_total_testing_daterange_str(self):
        wfo_cycles_list = list(self.wfo_cycles_dict.values())
        first_cycle = wfo_cycles_list[0]
        last_cycle = wfo_cycles_list[-1]
        return self.getdaterange(first_cycle.testing_start_date, last_cycle.testing_end_date)

