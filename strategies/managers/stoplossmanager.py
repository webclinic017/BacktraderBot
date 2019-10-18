
NONE_TRADE_RESULT = 0
STOP_LOSS_TRIGGERED_TRADE_RESULT = 1
TRAILING_STOP_LOSS_TRIGGERED_TRADE_RESULT = 2


class StopLossManager(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.data = strategy.data
        self.debug = debug

        self.is_sl_enabled = self.strategy.p.sl is not None
        self.is_trailing_mode = self.strategy.p.tslflag is not None
        self.is_sl_activated = False

        self.sl_price = None
        self.trailed_price = None

        self.trade_result = NONE_TRADE_RESULT

    def is_activated(self):
        return self.is_sl_activated is True

    def is_long_trade(self, trade):
        return True if trade.size >= 0 else False

    def open_trade(self, trade):
        self.trade_result = NONE_TRADE_RESULT
        if self.is_sl_enabled is True:
            self.activate_sl(trade)

    def activate_sl(self, trade):
        if self.is_sl_activated is not True:
            is_long = self.is_long_trade(trade)
            base_price = trade.price
            self.sl_price = self.get_sl_price(base_price, self.strategy.p.sl, is_long)
            self.is_sl_activated = True
            if self.is_trailing_mode is True:
                self.trailed_price = trade.price
                self.strategy.log("Activated TRAILING STOP-LOSS for trade.tradeid={}, base_price={}, self.trailed_price={}, self.sl_price={}".format(trade.tradeid, base_price, self.trailed_price, self.sl_price))
            else:
                self.strategy.log("Activated STOP-LOSS for trade.tradeid={}, base_price={}, self.sl_price={}".format(trade.tradeid, base_price, self.sl_price))

    def move_tsl(self, last_price, is_long):
        if is_long is True and last_price > self.trailed_price or \
           is_long is False and last_price < self.trailed_price:
            old_trailed_price = self.trailed_price
            old_sl_price = self.sl_price
            self.trailed_price = last_price
            self.sl_price = self.get_sl_price(last_price, self.strategy.p.sl, is_long)
            self.strategy.log("Moved TRAILING STOP-LOSS targets: self.trailed_price={} -> {}, self.sl_price={} -> {}, last_price={}, is_long={}".format(old_trailed_price, self.trailed_price, old_sl_price, self.sl_price, last_price, is_long))

    def set_trade_result(self):
        if self.is_sl_activated and self.is_trailing_mode is True:
            self.trade_result = TRAILING_STOP_LOSS_TRIGGERED_TRADE_RESULT

        if self.is_sl_activated and self.is_trailing_mode is False:
            self.trade_result = STOP_LOSS_TRIGGERED_TRADE_RESULT

    def process_next(self):
        if self.is_sl_enabled is False and self.is_trailing_mode is False or \
           self.strategy.is_position_closed() or self.is_sl_activated is not True:
            return

        is_long = self.strategy.is_long_position()
        last_price = self.data.close[0]
        if self.is_sl_reached(self.sl_price, last_price, is_long):
            if self.is_trailing_mode is True:
                self.strategy.log("Price has reached TRAILING STOP-LOSS target, closing the position: self.sl_price={}, last_price={}, is_long={}".format(self.sl_price, last_price, is_long))
            else:
                self.strategy.log("Price has reached STOP-LOSS target, closing the position: self.sl_price={}, last_price={}, is_long={}".format(self.sl_price, last_price, is_long))
            self.strategy.close_position(self.strategy.curr_position, self.strategy.broker.getcash(), is_long)
            self.set_trade_result()
            return

        if self.is_trailing_mode is True:
            self.move_tsl(last_price, is_long)

    def deactivate_sl(self, trade):
        self.is_sl_activated = False

    def close_trade(self, trade):
        self.deactivate_sl(trade)
        if self.is_trailing_mode is True:
            self.strategy.log('StopLossManager.close_trade() - TRAILING STOP-LOSS has been deactivated')
        else:
            self.strategy.log('StopLossManager.close_trade() - STOP-LOSS has been deactivated')

    def is_sl_reached(self, sl_price, last_price, is_long):
        result = False
        if is_long is True and last_price < sl_price or \
           is_long is False and last_price > sl_price:
            result = True
        return result

    def get_sl_price(self, base_price, sl_dist_pct, is_long):
        if is_long is True:
            return base_price * (1 - sl_dist_pct / 100.0)
        else:
            return base_price * (1 + sl_dist_pct / 100.0)

    def is_sl_triggered_trade_result(self):
        return self.trade_result == STOP_LOSS_TRIGGERED_TRADE_RESULT

    def is_tsl_triggered_trade_result(self):
        return self.trade_result == TRAILING_STOP_LOSS_TRIGGERED_TRADE_RESULT
