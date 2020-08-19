from strategies.helper.constants import TradeExitMode

DEFAULT_MIN_SL_ATR_MULT = 2
DEFAULT_MIN_TP_ATR_MULT = 2
MAXIMUM_ALLOWED_SL_PCT = 20


class DailyRangePriceStats(object):
    def __init__(self):
        self.k1 = 0
        self.k2 = 0
        self.hrd = 0
        self.hrc = 0
        self.halfrangedeltapct = 0


class SLTPCalculator(object):

    def __init__(self, strategy):
        self.strategy = strategy
        self.data = strategy.data
        self.exitmode = self.strategy.p.exitmode
        self.sl_pct = self.strategy.p.sl
        self.tsl_pct = self.strategy.p.sl
        self.tp_pct = self.strategy.p.tp
        self.ttp_pct = self.strategy.p.ttpdist
        self.tb_dist_pct = self.strategy.p.tbdist

    def calc_low_side_pr(self, base_price, val_pct, is_long):
        if is_long:
            return round(base_price * (1 - val_pct / 100.0), 8)
        else:
            return round(base_price * (1 + val_pct / 100.0), 8)

    def calc_high_side_pr(self, base_price, val_pct, is_long):
        if is_long:
            return round(base_price * (1 + val_pct / 100.0), 8)
        else:
            return round(base_price * (1 - val_pct / 100.0), 8)

    def get_sl_price(self, base_price, is_long):
        if self.exitmode == TradeExitMode.EXIT_MODE_DEFAULT:
            return self.calc_low_side_pr(base_price, self.sl_pct, is_long)
        elif self.exitmode == TradeExitMode.EXIT_MODE_SET_DYNAMIC_SLTP_WITH_ATR:
            atr_mult = self.sl_pct
            sl_pct = self.strategy.atr_tf_pct[0] * atr_mult
            self.strategy.log("SLTPCalculator.get_sl_price(): self.exitmode={}, atr_mult={}, sl_pct={:.2f}%".format(self.exitmode, atr_mult, sl_pct))
            return self.calc_low_side_pr(base_price, sl_pct, is_long)

    def get_tp_price(self, base_price, is_long):
        if self.exitmode == TradeExitMode.EXIT_MODE_DEFAULT:
            return self.calc_high_side_pr(base_price, self.tp_pct, is_long)
        elif self.exitmode == TradeExitMode.EXIT_MODE_SET_DYNAMIC_SLTP_WITH_ATR:
            atr_mult = self.tp_pct
            tp_pct = self.strategy.atr_tf_pct[0] * atr_mult
            self.strategy.log("SLTPCalculator.get_tp_price(): self.exitmode={}, atr_mult={}, tp_pct={:.2f}%".format(self.exitmode, atr_mult, tp_pct))
            return self.calc_high_side_pr(base_price, tp_pct, is_long)

    def get_ttp_price(self, base_price, is_long):
        if self.exitmode == TradeExitMode.EXIT_MODE_DEFAULT:
            return self.calc_low_side_pr(base_price, self.ttp_pct, is_long)
        elif self.exitmode == TradeExitMode.EXIT_MODE_SET_DYNAMIC_SLTP_WITH_ATR:
            atr_mult = self.ttp_pct
            ttp_pct = self.strategy.atr_tf_pct[0] * atr_mult
            self.strategy.log("SLTPCalculator.get_ttp_price(): self.exitmode={}, atr_mult={}, ttp_pct={:.2f}%".format(self.exitmode, atr_mult, ttp_pct))
            return self.calc_low_side_pr(base_price, ttp_pct, is_long)

    def get_tb_price(self, is_long, base_price):
        if self.exitmode == TradeExitMode.EXIT_MODE_DEFAULT:
            return self.calc_high_side_pr(base_price, self.tb_dist_pct, is_long)
        elif self.exitmode == TradeExitMode.EXIT_MODE_SET_DYNAMIC_SLTP_WITH_ATR:
            atr_mult = self.tb_dist_pct
            tb_dist_pct = self.strategy.atr_tf_pct[0] * atr_mult
            self.strategy.log("SLTPCalculator.get_tb_price(): self.exitmode={}, atr_mult={}, tb_dist_pct={:.2f}%".format(self.exitmode, atr_mult, tb_dist_pct))
            return self.calc_high_side_pr(base_price, tb_dist_pct, is_long)

    def get_price_move_delta_pct(self, price1, price2):
        return abs(100 * (price1 - price2) / price2)
