
NONE_TRADE_RESULT = 0
TAKE_PROFIT_TRIGGERED_TRADE_RESULT = 1
TRAILING_TAKE_PROFIT_TRIGGERED_TRADE_RESULT = 2


class TakeProfitManager(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.data = strategy.data
        self.debug = debug

        self.is_tp_enabled = self.strategy.p.tp is not None
        self.is_trailing_mode = self.strategy.p.ttpdist is not None

        self.is_tp_activated = False
        self.is_ttp_activated = False

        self.tp_price = None
        self.trailed_price = None
        self.ttp_price = None

        self.trade_result = NONE_TRADE_RESULT

    def is_activated(self):
        return self.is_tp_activated is True or self.is_ttp_activated is True

    def is_long_trade(self, trade):
        return True if trade.size >= 0 else False

    def open_trade(self, trade):
        self.trade_result = NONE_TRADE_RESULT
        if self.is_tp_enabled is True:
            self.activate_tp(trade)

    def activate_tp(self, trade):
        if self.is_tp_activated is not True and self.is_ttp_activated is not True:
            is_long = self.is_long_trade(trade)
            base_price = trade.price
            self.tp_price = self.get_tp_price(base_price, self.strategy.p.tp, is_long)
            self.is_tp_activated = True
            self.strategy.log("Activated TAKE-PROFIT for trade.tradeid={}, base_price={}, self.tp_price={}".format(trade.tradeid, base_price, self.tp_price))

    def activate_ttp(self, base_price, is_long):
        if self.is_tp_activated is True and self.is_ttp_activated is not True:
            self.trailed_price = base_price
            self.ttp_price = self.get_ttp_price(base_price, self.strategy.p.ttpdist, is_long)
            self.is_ttp_activated = True
            self.strategy.log("Activated TRAILING TAKE-PROFIT for base_price={}, self.trailed_price={}, self.ttp_price={}".format(base_price, self.trailed_price, self.ttp_price))

    def move_ttp(self, last_price, is_long):
        if is_long is True and last_price > self.trailed_price or \
           is_long is False and last_price < self.trailed_price:
            old_trailed_price = self.trailed_price
            old_ttp_price = self.ttp_price
            self.trailed_price = last_price
            self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
            self.strategy.log("Moved TRAILING TAKE-PROFIT targets: self.trailed_price={} -> {}, self.ttp_price={} -> {}, last_price={}, is_long={}".format(old_trailed_price, self.trailed_price, old_ttp_price, self.ttp_price, last_price, is_long))

    def set_trade_result(self):
        if self.is_tp_activated is True and self.is_ttp_activated is False:
            self.trade_result = TAKE_PROFIT_TRIGGERED_TRADE_RESULT

        if self.is_tp_activated is True and self.is_ttp_activated is True:
            self.trade_result = TRAILING_TAKE_PROFIT_TRIGGERED_TRADE_RESULT

    def process_next(self):
        if self.is_tp_enabled is False and self.is_trailing_mode is False or \
           self.strategy.is_position_closed() or self.is_tp_activated is not True:
            return

        is_long = self.strategy.is_long_position()
        last_price = self.data.close[0]
        if self.is_tp_activated is True and self.is_ttp_activated is False:
            if self.is_tp_reached(self.tp_price, last_price, is_long):
                if self.is_trailing_mode is False:
                    self.strategy.log("Price has reached TAKE-PROFIT target, closing the position: self.tp_price={}, last_price={}, is_long={}".format(self.tp_price, last_price, is_long))
                    self.strategy.close_position(self.strategy.curr_position, self.strategy.broker.getcash(), is_long)
                    self.set_trade_result()
                    return
                else:
                    self.strategy.log("Price has reached TAKE-PROFIT target and activating TRAILING mode: self.tp_price={}, last_price={}, is_long={}".format(self.tp_price, last_price, is_long))
                    self.activate_ttp(last_price, is_long)
                    return

        if self.is_tp_activated is True and self.is_ttp_activated is True:
            if self.is_ttp_reached(self.ttp_price, last_price, is_long):
                self.strategy.log("Price has reached TRAILING TAKE-PROFIT target, closing the position: self.ttp_price={}, last_price={}, is_long={}".format(self.ttp_price, last_price, is_long))
                self.strategy.close_position(self.strategy.curr_position, self.strategy.broker.getcash(), is_long)
                self.set_trade_result()
                return
            else:
                self.move_ttp(last_price, is_long)

    def deactivate_tp(self, trade):
        self.is_tp_activated = False
        self.is_ttp_activated = False

    def close_trade(self, trade):
        prev_is_tp_activated = self.is_tp_activated
        prev_is_ttp_activated = self.is_ttp_activated
        self.deactivate_tp(trade)
        if prev_is_tp_activated:
            self.strategy.log('TakeProfitManager.close_trade() - TAKE-PROFIT has been deactivated')
        if prev_is_ttp_activated:
            self.strategy.log('TakeProfitManager.close_trade() - TRAILING TAKE-PROFIT has been deactivated')

    def is_tp_reached(self, tp_price, last_price, is_long):
        result = False
        if is_long is True and last_price > tp_price or \
           is_long is False and last_price < tp_price:
            result = True
        return result

    def is_ttp_reached(self, tp_price, last_price, is_long):
        result = False
        if is_long is True and last_price < tp_price or \
           is_long is False and last_price > tp_price:
            result = True
        return result

    def get_tp_price(self, base_price, tp_dist_pct, is_long):
        if is_long is True:
            return base_price * (1 + tp_dist_pct / 100.0)
        else:
            return base_price * (1 - tp_dist_pct / 100.0)

    def get_ttp_price(self, base_price, ttp_dist_pct, is_long):
        if is_long is True:
            return base_price * (1 - ttp_dist_pct / 100.0)
        else:
            return base_price * (1 + ttp_dist_pct / 100.0)

    def is_tp_triggered_trade_result(self):
        return self.trade_result == TAKE_PROFIT_TRIGGERED_TRADE_RESULT

    def is_ttp_triggered_trade_result(self):
        return self.trade_result == TRAILING_TAKE_PROFIT_TRIGGERED_TRADE_RESULT
