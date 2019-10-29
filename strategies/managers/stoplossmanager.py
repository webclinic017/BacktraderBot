import backtrader as bt


class StopLossManager(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.data = strategy.data
        self.debug = debug
        self.strategy_analyzers = strategy.analyzers

        self._is_sl_enabled = self.strategy.p.sl is not None
        self.is_trailing_mode = self.strategy.p.tslflag is not None
        self.is_sl_activated = False

        self.tradeid = None
        self.sl_order = None
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

    def submit_new_sl_order(self, is_long, tradeid, sl_size, sl_price):
        if is_long:
            sl_order = self.strategy.generic_sell(tradeid=tradeid, size=sl_size, price=sl_price, exectype=bt.Order.Stop)
            self.strategy.log('Submitted a new {} order (SELL STOP MARKET): tradeid={}, sl_price={}, sl_order.ref={}, sl_order.size={}, sl_order.price={}, sl_order.side={}'.format(self.get_sl_type_str(), tradeid, sl_price, sl_order.ref, sl_order.size, sl_order.price, sl_order.ordtypename()))
        else:
            sl_order = self.strategy.generic_buy(tradeid=tradeid, size=sl_size, price=sl_price, exectype=bt.Order.Stop)
            self.strategy.log('Submitted a new {} order (BUY STOP MARKET): tradeid={}, sl_price={}, sl_order.ref={}, sl_order.size={}, sl_order.price={}, sl_order.side={}'.format(self.get_sl_type_str(), tradeid, sl_price, sl_order.ref, sl_order.size, sl_order.price, sl_order.ordtypename()))
        return sl_order

    def cancel_sl_order(self):
        if self.is_activated() and self.sl_order:
            self.strategy.cancel(self.sl_order)
            self.strategy.log("Cancelled the current {} order: self.sl_order.ref={}".format(self.get_sl_type_str(), self.sl_order.ref))
            self.sl_order = None

    def activate(self, tradeid, pos_price, pos_size, is_long):
        if self.is_sl_enabled() and not self.is_sl_activated:
            self.tradeid = tradeid
            self.sl_price = self.get_sl_price(pos_price, self.strategy.p.sl, is_long)
            self.sl_order = self.submit_new_sl_order(is_long, self.tradeid, pos_size, self.sl_price)
            self.is_sl_activated = True
            if self.is_trailing_mode:
                self.trailed_price = pos_price
                self.strategy.log("Activated {} for self.tradeid={}, self.sl_order.ref={}, self.sl_order.size={}, self.sl_order.price={}, pos_price={}, pos_size={}, self.trailed_price={}, self.sl_price={}".format(self.get_sl_type_str(), self.tradeid, self.sl_order.ref, self.sl_order.size, self.sl_order.price, pos_price, pos_size, self.trailed_price, self.sl_price))
            else:
                self.strategy.log("Activated {} for self.tradeid={}, self.sl_order.ref={}, self.sl_order.size={}, self.sl_order.price={}, pos_price={}, pos_size={}, self.sl_price={}".format(self.get_sl_type_str(), self.tradeid, self.sl_order.ref, self.sl_order.size, self.sl_order.price, pos_price, pos_size, self.sl_price))

    def move_tsl(self, last_price, is_long):
        if is_long and last_price > self.trailed_price or not is_long and last_price < self.trailed_price:
            old_trailed_price = self.trailed_price
            sl_size = self.sl_order.size
            old_sl_price = self.sl_price
            self.trailed_price = last_price
            self.sl_price = self.get_sl_price(last_price, self.strategy.p.sl, is_long)
            self.strategy.log("Moving TRAILING STOP-LOSS targets: self.trailed_price={} -> {}, self.sl_price={} -> {}, last_price={}, sl_size={}, is_long={}".format(old_trailed_price, self.trailed_price, old_sl_price, self.sl_price, last_price, sl_size, is_long))
            self.cancel_sl_order()
            self.sl_order = self.submit_new_sl_order(is_long, self.tradeid, sl_size, self.sl_price)
            self.strategy_analyzers.ta.update_moved_tsl_counts_data(self.is_trailing_mode)

    def on_next(self):
        if not self.is_sl_enabled() and not self.is_trailing_mode or self.strategy.is_position_closed() or not self.is_sl_activated:
            return

        if self.is_trailing_mode:
            is_long = self.strategy.is_long_position()
            last_price = self.data.close[0]
            self.move_tsl(last_price, is_long)

    def handle_order_completed(self, order):
        if order.status == order.Completed and self.sl_order and self.sl_order.ref == order.ref:
            self.strategy.log('StopLossManager.handle_order_completed(): order.ref={}, status={}'.format(order.ref, order.getstatusname()))
            self.strategy.log("The {} order has been triggered and COMPLETED: self.sl_order.ref={}, self.trailed_price={}, self.sl_price={}, order.price={}, order.size={}".format(self.get_sl_type_str(), self.sl_order.ref, self.trailed_price, self.sl_price, order.price, order.size))
            self.deactivate(False)
            self.strategy_analyzers.ta.update_sl_counts_data(self.is_trailing_mode)
            return True
        return False

    def deactivate(self, is_cancel_sl_order):
        if self.is_sl_enabled() and self.is_activated():
            if is_cancel_sl_order:
                self.cancel_sl_order()
            self.is_sl_activated = False
            self.strategy.log('StopLossManager.deactivate() - {} has been deactivated'.format(self.get_sl_type_str()))

    def is_sl_reached(self, sl_price, last_price, is_long):
        result = False
        if is_long is True and last_price < sl_price or \
           is_long is False and last_price > sl_price:
            result = True
        return result

    def get_sl_price(self, base_price, sl_dist_pct, is_long):
        if is_long:
            return base_price * (1 - sl_dist_pct / 100.0)
        else:
            return base_price * (1 + sl_dist_pct / 100.0)

