
class TakeProfitManager(object):

    def __init__(self, strategy, strategyprocessor, debug):
        self.strategy = strategy
        self.strategyprocessor = strategyprocessor
        self.data = strategy.data
        self.debug = debug
        self.strategy_analyzers = strategy.analyzers

        self._is_tp_enabled = self.strategy.p.tp is not None
        self.is_trailing_mode = self.strategy.p.ttpdist is not None

        self.is_tp_activated = False
        self.is_ttp_activated = False

        self.tp_price = None
        self.trailed_price = None
        self.ttp_order = None
        self.ttp_price = None

    def get_order_type_str(self, order):
        if order.isbuy():
            return "BUY"
        if order.issell():
            return "SELL"
        else:
            raise Exception("Wrong order state")

    def get_tp_type_str(self):
        return "TRAILING TAKE-PROFIT" if self.is_trailing_mode else "TAKE-PROFIT"

    def is_tp_enabled(self):
        return self._is_tp_enabled

    def is_activated(self):
        return self.is_tp_activated or self.is_ttp_activated

    def is_long_order(self, order):
        return True if order.size >= 0 else False

    def activate(self, pos_price, is_long):
        if self.is_tp_enabled() and not self.is_tp_activated and not self.is_ttp_activated:
            self.tp_price = self.get_tp_price(pos_price, self.strategy.p.tp, is_long)
            self.is_tp_activated = True
            self.strategy.log("Activated TAKE-PROFIT mode for pos_price={}, self.tp_price={}".format(pos_price, self.tp_price))

    def activate_ttp(self, last_price, is_long):
        if self.is_tp_activated and not self.is_ttp_activated:
            self.trailed_price = last_price
            self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
            self.is_ttp_activated = True
            self.strategy.log("Activated TRAILING TAKE-PROFIT mode for last_price={}, self.trailed_price={}, self.ttp_price={}".format(last_price, self.trailed_price, self.ttp_price))

    def move_ttp(self, last_price, is_long):
        if is_long and last_price > self.trailed_price or not is_long and last_price < self.trailed_price:
            old_trailed_price = self.trailed_price
            old_ttp_price = self.ttp_price
            self.trailed_price = last_price
            self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
            self.strategy.log("Moving TRAILING TAKE-PROFIT targets: self.trailed_price={} -> {}, self.ttp_price={} -> {}, last_price={}, is_long={}".format(old_trailed_price, self.trailed_price, old_ttp_price, self.ttp_price, last_price, is_long))
            self.strategy_analyzers.ta.update_moved_ttp_counts_data(self.is_trailing_mode)

    def on_next(self):
        if not self.is_tp_enabled() and not self.is_trailing_mode or self.strategy.is_position_closed() or not self.is_tp_activated:
            return False

        is_long = self.strategy.is_long_position()
        last_price = self.data.close[0]
        if not self.is_trailing_mode:
            if self.is_tp_activated and not self.is_ttp_activated:
                if self.is_tp_reached(last_price, self.tp_price, is_long):
                    self.strategy.log("Price has reached TAKE-PROFIT target, closing the position: self.tp_price={}, last_price={}, is_long={}".format(self.tp_price, last_price, is_long))
                    self.strategyprocessor.close_position()
                    self.deactivate()
                    self.strategy_analyzers.ta.update_tp_counts_data(self.is_trailing_mode)
                    return True
        else:
            if self.is_tp_activated and not self.is_ttp_activated:
                if self.is_tp_reached(last_price, self.tp_price, is_long):
                    self.strategy.log("Price has reached TAKE-PROFIT target and activating TRAILING TAKE-PROFIT mode: self.tp_price={}, last_price={}, is_long={}".format(self.tp_price, last_price, is_long))
                    self.activate_ttp(last_price, is_long)
                    return False

            if self.is_tp_activated and self.is_ttp_activated:
                if self.is_ttp_reached(last_price, self.ttp_price, is_long):
                    self.strategy.log("Price has reached TRAILING TAKE-PROFIT target, closing the position: self.ttp_price={}, last_price={}, is_long={}".format(self.ttp_price, last_price, is_long))
                    self.strategyprocessor.close_position()
                    self.deactivate()
                    self.strategy_analyzers.ta.update_tp_counts_data(self.is_trailing_mode)
                    return True
                else:
                    self.move_ttp(last_price, is_long)
                    return False

    def deactivate(self):
        if self.is_tp_enabled() and self.is_activated():
            self.is_tp_activated = False
            self.is_ttp_activated = False
            self.strategy.log('TakeProfitManager.deactivate() - {} has been deactivated'.format(self.get_tp_type_str()))

    def is_tp_reached(self, last_price, tp_price, is_long):
        result = False
        if is_long and last_price > tp_price or not is_long and last_price < tp_price:
            result = True
        return result

    def is_ttp_reached(self, last_price, tp_price, is_long):
        result = False
        if is_long and last_price < tp_price or not is_long and last_price > tp_price:
            result = True
        return result

    def get_tp_price(self, base_price, tp_dist_pct, is_long):
        if is_long:
            return base_price * (1 + tp_dist_pct / 100.0)
        else:
            return base_price * (1 - tp_dist_pct / 100.0)

    def get_ttp_price(self, base_price, ttp_dist_pct, is_long):
        if is_long:
            return base_price * (1 - ttp_dist_pct / 100.0)
        else:
            return base_price * (1 + ttp_dist_pct / 100.0)

