import backtrader as bt


class TakeProfitManager(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.data = strategy.data
        self.debug = debug
        self.strategy_analyzers = strategy.analyzers

        self._is_tp_enabled = self.strategy.p.tp is not None
        self.is_trailing_mode = self.strategy.p.ttpdist is not None

        self.is_tp_activated = False
        self.is_ttp_activated = False

        self.tradeid = None
        self.tp_order = None
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

    def submit_new_tp_order(self, is_long, tradeid, tp_size, tp_price):
        if is_long:
            tp_order = self.strategy.generic_sell(tradeid=tradeid, size=tp_size, price=tp_price, exectype=bt.Order.Limit)
            self.strategy.log('Submitted a new TAKE-PROFIT order (SELL LIMIT): tradeid={}, tp_price={}, tp_order.ref={}, tp_order.size={}, tp_order.price={}, tp_order.side={}'.format(tradeid, tp_price, tp_order.ref, tp_order.size, tp_order.price, tp_order.ordtypename()))
        else:
            tp_order = self.strategy.generic_buy(tradeid=tradeid, size=tp_size, price=tp_price, exectype=bt.Order.Limit)
            self.strategy.log('Submitted a new TAKE-PROFIT order (BUY LIMIT): tradeid={}, tp_price={}, tp_order.ref={}, tp_order.size={}, tp_order.price={}, tp_order.side={}'.format(tradeid, tp_price, tp_order.ref, tp_order.size, tp_order.price, tp_order.ordtypename()))
        return tp_order

    def submit_new_ttp_order(self, is_long, tradeid, ttp_size, ttp_price):
        if is_long:
            ttp_order = self.strategy.generic_sell(tradeid=tradeid, size=ttp_size, price=ttp_price, exectype=bt.Order.Stop)
            self.strategy.log('Submitted a new TRAILING TAKE-PROFIT order (SELL STOP MARKET): tradeid={}, ttp_price={}, ttp_order.ref={}, ttp_order.size={}, ttp_order.price={}, ttp_order.side={}'.format(tradeid, ttp_price, ttp_order.ref, ttp_order.size, ttp_order.price, ttp_order.ordtypename()))
        else:
            ttp_order = self.strategy.generic_buy(tradeid=tradeid, size=ttp_size, price=ttp_price, exectype=bt.Order.Stop)
            self.strategy.log('Submitted a new TRAILING TAKE-PROFIT order (BUY STOP MARKET): tradeid={}, ttp_price={}, ttp_order.ref={}, ttp_order.size={}, ttp_order.price={}, ttp_order.side={}'.format(tradeid, ttp_price, ttp_order.ref, ttp_order.size, ttp_order.price, ttp_order.ordtypename()))
        return ttp_order

    def cancel_tp_order(self):
        if self.is_activated() and self.tp_order:
            self.strategy.cancel(self.tp_order)
            self.strategy.log("Cancelled the current {} order: self.tp_order.ref={}".format(self.get_tp_type_str(), self.tp_order.ref))
            self.tp_order = None

    def cancel_ttp_order(self):
        if self.is_activated() and self.ttp_order:
            self.strategy.cancel(self.ttp_order)
            self.strategy.log("Cancelled the current {} order: self.ttp_order.ref={}".format(self.get_tp_type_str(), self.ttp_order.ref))
            self.ttp_order = None

    def activate(self, tradeid, pos_price, pos_size, is_long):
        if self.is_tp_enabled() and not self.is_tp_activated and not self.is_ttp_activated:
            self.tradeid = tradeid
            self.tp_price = self.get_tp_price(pos_price, self.strategy.p.tp, is_long)
            if not self.is_trailing_mode:
                self.tp_order = self.submit_new_tp_order(is_long, self.tradeid, pos_size, self.tp_price)
                self.is_tp_activated = True
                self.strategy.log("Activated TAKE-PROFIT mode for self.tp_order.ref={}, self.tp_order.size={}, self.tp_order.price={}, pos_price={}, pos_size={}, self.tp_price={}".format(self.tp_order.ref, self.tp_order.size, self.tp_order.price, pos_price, pos_size, self.tp_price))
            else:
                self.is_tp_activated = True
                self.strategy.log("Prepared for TRAILING TAKE-PROFIT mode for pos_price={}, pos_size={}, self.tp_price={}".format(pos_price, pos_size, self.tp_price))

    def activate_ttp(self, tradeid, pos_size, last_price, is_long):
        if self.is_tp_activated and not self.is_ttp_activated:
            self.trailed_price = last_price
            self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
            self.ttp_order = self.submit_new_ttp_order(is_long, tradeid, pos_size, self.ttp_price)
            self.is_ttp_activated = True
            self.strategy.log("Activated TRAILING TAKE-PROFIT mode for pos_size={}, last_price={}, self.trailed_price={}, self.ttp_price={}".format(pos_size, last_price, self.trailed_price, self.ttp_price))

    def move_ttp(self, tradeid, last_price, is_long):
        if is_long and last_price > self.trailed_price or not is_long and last_price < self.trailed_price:
            ttp_size = self.ttp_order.size
            old_trailed_price = self.trailed_price
            old_ttp_price = self.ttp_price
            self.trailed_price = last_price
            self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
            self.strategy.log("Moving TRAILING TAKE-PROFIT targets: self.trailed_price={} -> {}, self.ttp_price={} -> {}, last_price={}, ttp_size={}, is_long={}".format(old_trailed_price, self.trailed_price, old_ttp_price, self.ttp_price, last_price, ttp_size, is_long))
            self.cancel_ttp_order()
            self.ttp_order = self.submit_new_ttp_order(is_long, tradeid, ttp_size, self.ttp_price)
            self.strategy_analyzers.ta.update_moved_ttp_counts_data(self.is_trailing_mode)

    def on_next(self):
        if not self.is_tp_enabled() and not self.is_trailing_mode or self.strategy.is_position_closed() or not self.is_tp_activated:
            return

        is_long = self.strategy.is_long_position()
        last_price = self.data.close[0]
        if self.is_trailing_mode:
            if self.is_tp_activated and not self.is_ttp_activated:
                if self.is_tp_reached(self.tp_price, last_price, is_long):
                    self.strategy.log("Price has reached TAKE-PROFIT target and activating TRAILING TAKE-PROFIT mode: self.tp_price={}, last_price={}, is_long={}".format(self.tp_price, last_price, is_long))
                    pos_size = self.strategy.position.size
                    self.activate_ttp(self.tradeid, pos_size, last_price, is_long)
                    return

            if self.is_tp_activated and self.is_ttp_activated:
                self.move_ttp(self.tradeid, last_price, is_long)

    def handle_order_completed(self, order):
        if order.status == order.Completed and (self.tp_order and self.tp_order.ref == order.ref or self.ttp_order and self.ttp_order.ref == order.ref):
            self.strategy.log('TakeProfitManager.handle_order_completed(): order.ref={}, status={}'.format(order.ref, order.getstatusname()))
            if not self.is_trailing_mode:
                self.strategy.log("The {} order has been triggered and COMPLETED: self.tp_order.ref={}, self.trailed_price={}, self.tp_price={}, order.price={}, order.size={}".format(self.get_tp_type_str(), self.tp_order.ref, self.trailed_price, self.tp_price, order.price, order.size))
            else:
                self.strategy.log("The {} order has been triggered and COMPLETED: self.ttp_order.ref={}, self.trailed_price={}, self.ttp_price={}, order.price={}, order.size={}".format(self.get_tp_type_str(), self.ttp_order.ref, self.trailed_price, self.ttp_price, order.price, order.size))
            self.deactivate(False)
            self.strategy_analyzers.ta.update_tp_counts_data(self.is_trailing_mode)
            return True
        return False

    def deactivate(self, is_cancel_tp_orders):
        if self.is_tp_enabled() and self.is_activated():
            if is_cancel_tp_orders:
                self.cancel_tp_order()
                self.cancel_ttp_order()
            self.is_tp_activated = False
            self.is_ttp_activated = False
            self.strategy.log('TakeProfitManager.deactivate() - {} has been deactivated'.format(self.get_tp_type_str()))

    def is_tp_reached(self, tp_price, last_price, is_long):
        result = False
        if is_long and last_price > tp_price or not is_long and last_price < tp_price:
            result = True
        return result

    def is_ttp_reached(self, tp_price, last_price, is_long):
        result = False
        if is_long is True and last_price < tp_price or \
           is_long is False and last_price > tp_price:
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

