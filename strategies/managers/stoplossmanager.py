
class StopLossManager(object):

    def __init__(self, strategy, strategyprocessor, debug):
        self.strategy = strategy
        self.strategyprocessor = strategyprocessor
        self.data = strategy.data
        self.debug = debug
        self.strategy_analyzers = strategy.analyzers

        self._is_sl_enabled = self.strategy.p.sl is not None
        self.is_trailing_mode = self.strategy.p.tslflag is not None
        self.is_sl_activated = False

        self.sl_price = None
        self.trailed_price = None

    def get_order_type_str(self, order):
        if order.isbuy():
            return "BUY"
        if order.issell():
            return "SELL"
        else:
            raise Exception("Wrong order state")

    def get_sl_type_str(self):
        return "TRAILING STOP-LOSS" if self.is_trailing_mode else "STOP-LOSS"

    def is_sl_enabled(self):
        return self._is_sl_enabled

    def is_activated(self):
        return self.is_sl_activated

    def is_long_order(self, order):
        return True if order.size >= 0 else False

    def activate(self, pos_price, is_long):
        if self.is_sl_enabled() and not self.is_sl_activated:
            self.sl_price = self.get_sl_price(pos_price, self.strategy.p.sl, is_long)
            self.is_sl_activated = True
            if self.is_trailing_mode:
                self.trailed_price = pos_price
            self.strategy.log("Activated {} mode for pos_price={}, self.trailed_price={}, self.sl_price={}".format(self.get_sl_type_str(), pos_price, self.trailed_price, self.sl_price))

    def move_tsl(self, last_price, is_long):
        if is_long and last_price > self.trailed_price or not is_long and last_price < self.trailed_price:
            old_trailed_price = self.trailed_price
            old_sl_price = self.sl_price
            self.trailed_price = last_price
            self.sl_price = self.get_sl_price(last_price, self.strategy.p.sl, is_long)
            self.strategy.log("Moving TRAILING STOP-LOSS targets: self.trailed_price={} -> {}, self.sl_price={} -> {}, last_price={}, is_long={}".format(old_trailed_price, self.trailed_price, old_sl_price, self.sl_price, last_price, is_long))
            self.strategy_analyzers.ta.update_moved_tsl_counts_data(self.is_trailing_mode)

    def on_next(self):
        if not self.is_sl_enabled() and not self.is_trailing_mode or self.strategy.is_position_closed() or not self.is_sl_activated:
            return False

        is_long = self.strategy.is_long_position()
        last_price = self.data.close[0]
        if self.is_sl_reached(self.sl_price, last_price, is_long):
            self.strategy.log("Price has reached {} target, closing the position: self.sl_price={}, last_price={}, is_long={}".format(self.get_sl_type_str(), self.sl_price, last_price, is_long))
            self.strategyprocessor.close_position()
            self.deactivate()
            self.strategy_analyzers.ta.update_sl_counts_data(self.is_trailing_mode)
            return True

        if self.is_trailing_mode:
            is_long = self.strategy.is_long_position()
            last_price = self.data.close[0]
            self.move_tsl(last_price, is_long)
            return False

    def deactivate(self):
        if self.is_sl_enabled() and self.is_activated():
            self.is_sl_activated = False
            self.strategy.log('StopLossManager.deactivate() - {} has been deactivated'.format(self.get_sl_type_str()))

    def is_sl_reached(self, sl_price, last_price, is_long):
        result = False
        if is_long is True and last_price < sl_price or is_long is False and last_price > sl_price:
            result = True
        return result

    def get_sl_price(self, base_price, sl_dist_pct, is_long):
        if is_long:
            return base_price * (1 - sl_dist_pct / 100.0)
        else:
            return base_price * (1 + sl_dist_pct / 100.0)

