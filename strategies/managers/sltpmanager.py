import backtrader as bt

MOVE_TRAILING_PRICE_DELTA_THRESHOLD_PCT = 0.1


class SLTPManager(object):

    def __init__(self, strategy, oco_context):
        self.strategy = strategy
        self.oco_context = oco_context
        self.data = strategy.data
        self.strategy_analyzers = strategy.analyzers

        self.is_sl_enabled = self.strategy.p.sl is not None
        self.is_tsl_enabled = self.strategy.p.tslflag is not None
        self.is_tp_enabled = self.strategy.p.tp is not None
        self.is_ttp_enabled = self.strategy.p.ttpdist is not None

        self.is_sl_activated = False
        self.is_tp_activated = False
        self.is_ttp_activated = False

        self.tradeid = None
        self.sl_order = None
        self.sl_price = None
        self.sl_trailed_price = None
        self.tp_order = None
        self.tp_price = None
        self.tp_trailed_price = None
        self.ttp_price = None

    def get_order_type_str(self, order):
        if order.isbuy():
            return "BUY"
        if order.issell():
            return "SELL"
        else:
            raise Exception("Wrong order state")

    def get_sl_type_str(self):
        return "TRAILING STOP-LOSS" if self.is_tsl_enabled else "STOP-LOSS"

    def get_tp_type_str(self):
        return "TRAILING TAKE-PROFIT" if self.is_ttp_enabled else "TAKE-PROFIT"

    def is_sl_mode_activated(self):
        return self.is_sl_activated

    def is_tp_mode_activated(self):
        return self.is_tp_activated or self.is_ttp_activated

    def submit_new_sl_order(self, is_long, tradeid, sl_size, sl_price):
        if is_long:
            self.sl_order = self.strategy.generic_sell(tradeid=tradeid, size=sl_size, price=sl_price, exectype=bt.Order.Stop, oco=self.oco_context.get_tp_order())
            self.oco_context.set_sl_order(self.sl_order)
            self.strategy.log('Submitted a new {} order (SELL STOP MARKET): self.oco_context={}, tradeid={}, sl_size={}, sl_price={}, sl_order.ref={}, sl_order.size={}, sl_order.price={}, sl_order.side={}'.format(
                self.get_sl_type_str(), self.oco_context, tradeid, sl_size, sl_price, self.sl_order.ref, self.sl_order.size, self.sl_order.price, self.sl_order.ordtypename()))
        else:
            self.sl_order = self.strategy.generic_buy(tradeid=tradeid, size=sl_size, price=sl_price, exectype=bt.Order.Stop, oco=self.oco_context.get_tp_order())
            self.oco_context.set_sl_order(self.sl_order)
            self.strategy.log('Submitted a new {} order (BUY STOP MARKET): self.oco_context={}, tradeid={}, sl_size={}, sl_price={}, sl_order.ref={}, sl_order.size={}, sl_order.price={}, sl_order.side={}'.format(
                self.get_sl_type_str(), self.oco_context, tradeid, sl_size, sl_price, self.sl_order.ref, self.sl_order.size, self.sl_order.price, self.sl_order.ordtypename()))

    def submit_new_tp_order(self, is_long, tradeid, tp_size, tp_price):
        if is_long:
            self.tp_order = self.strategy.generic_sell(tradeid=tradeid, size=tp_size, price=tp_price, exectype=bt.Order.Limit, oco=self.oco_context.get_sl_order())
            self.oco_context.set_tp_order(self.tp_order)
            self.strategy.log('Submitted a new TAKE-PROFIT order (SELL LIMIT): self.oco_context={}, tradeid={}, tp_size={}, tp_price={}, self.tp_order.ref={}, self.tp_order.size={}, self.tp_order.price={}, self.tp_order.side={}'.format(
                self.oco_context, tradeid, tp_size, tp_price, self.tp_order.ref, self.tp_order.size, self.tp_order.price, self.tp_order.ordtypename()))
        else:
            self.tp_order = self.strategy.generic_buy(tradeid=tradeid, size=tp_size, price=tp_price, exectype=bt.Order.Limit, oco=self.oco_context.get_sl_order())
            self.oco_context.set_tp_order(self.tp_order)
            self.strategy.log('Submitted a new TAKE-PROFIT order (BUY LIMIT): self.oco_context={}, tradeid={}, tp_size={}, tp_price={}, self.tp_order.ref={}, self.tp_order.size={}, self.tp_order.price={}, self.tp_order.side={}'.format(
                self.oco_context, tradeid, tp_size, tp_price, self.tp_order.ref, self.tp_order.size, self.tp_order.price, self.tp_order.ordtypename()))

    def submit_new_ttp_order(self, is_long, tradeid, ttp_size, ttp_price):
        if is_long:
            self.tp_order = self.strategy.generic_sell(tradeid=tradeid, size=ttp_size, price=ttp_price, exectype=bt.Order.Stop, oco=self.oco_context.get_sl_order())
            self.oco_context.set_tp_order(self.tp_order)
            self.strategy.log('Submitted a new TRAILING TAKE-PROFIT order (SELL STOP MARKET): self.oco_context={}, tradeid={}, ttp_size={}, ttp_price={}, self.tp_order.ref={}, self.tp_order.size={}, self.tp_order.price={}, self.tp_order.side={}'.format(
                self.oco_context, tradeid, ttp_size, ttp_price, self.tp_order.ref, self.tp_order.size, self.tp_order.price, self.tp_order.ordtypename()))
        else:
            self.tp_order = self.strategy.generic_buy(tradeid=tradeid, size=ttp_size, price=ttp_price, exectype=bt.Order.Stop, oco=self.oco_context.get_sl_order())
            self.oco_context.set_tp_order(self.tp_order)
            self.strategy.log('Submitted a new TRAILING TAKE-PROFIT order (BUY STOP MARKET): self.oco_context={}, tradeid={}, ttp_size={}, ttp_price={}, self.tp_order.ref={}, self.tp_order.size={}, self.tp_order.price={}, self.tp_order.side={}'.format(
                self.oco_context, tradeid, ttp_size, ttp_price, self.tp_order.ref, self.tp_order.size, self.tp_order.price, self.tp_order.ordtypename()))

    def sl_oco_resubmit_order(self, old_order, is_long):
        if self.is_sl_enabled and self.is_sl_mode_activated():
            self.submit_new_sl_order(is_long, self.tradeid, old_order.size, old_order.price)

    def tp_oco_resubmit_order(self, old_order, is_long):
        if self.is_tp_enabled:
            if self.is_tp_activated and not self.is_ttp_activated:
                self.submit_new_tp_order(is_long, self.tradeid, old_order.size, old_order.price)
            if self.is_tp_activated and self.is_ttp_activated:
                self.submit_new_ttp_order(is_long, self.tradeid, old_order.size, old_order.price)

    def activate_sl(self, tradeid, pos_price, pos_size, is_long):
        if self.is_sl_enabled and not self.is_sl_activated:
            self.tradeid = tradeid
            self.sl_price = self.get_sl_price(pos_price, self.strategy.p.sl, is_long)
            self.submit_new_sl_order(is_long, self.tradeid, pos_size, self.sl_price)
            self.is_sl_activated = True
            if self.is_tsl_enabled:
                self.sl_trailed_price = pos_price
            self.strategy.log("Activated {} mode for self.oco_context={}, self.tradeid={}, self.sl_order.ref={}, self.sl_order.size={}, self.sl_order.price={}, pos_price={}, pos_size={}, self.trailed_price={}, self.sl_price={}".format(
                self.get_sl_type_str(), self.oco_context, self.tradeid, self.sl_order.ref, self.sl_order.size, self.sl_order.price, pos_price, pos_size, self.sl_trailed_price, self.sl_price))

    def activate_tp(self, tradeid, pos_price, pos_size, is_long):
        if self.is_tp_enabled and not self.is_tp_activated and not self.is_ttp_activated:
            self.tradeid = tradeid
            self.tp_price = self.get_tp_price(pos_price, self.strategy.p.tp, is_long)
            if not self.is_ttp_enabled:
                self.submit_new_tp_order(is_long, self.tradeid, pos_size, self.tp_price)
                self.is_tp_activated = True
                self.strategy.log("Activated TAKE-PROFIT mode for self.oco_context={}, self.tradeid={}, self.tp_order.ref={}, self.tp_order.size={}, self.tp_order.price={}, pos_price={}, pos_size={}, self.tp_price={}".format(
                    self.oco_context, self.tradeid, self.tp_order.ref, self.tp_order.size, self.tp_order.price, pos_price, pos_size, self.tp_price))
            else:
                self.is_tp_activated = True
                self.strategy.log("Prepared for TRAILING TAKE-PROFIT mode for self.oco_context={}, self.tradeid={}, pos_price={}, pos_size={}, self.tp_price={}".format(
                    self.oco_context, self.tradeid, pos_price, pos_size, self.tp_price))

    def activate_ttp(self, tradeid, pos_size, last_price, is_long):
        if self.is_tp_activated and not self.is_ttp_activated:
            self.tp_trailed_price = last_price
            self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
            self.submit_new_ttp_order(is_long, tradeid, pos_size, self.ttp_price)
            self.is_ttp_activated = True
            self.strategy.log("Activated TRAILING TAKE-PROFIT mode for self.oco_context={}, self.tradeid={}, self.tp_order.ref={}, self.tp_order.size={}, self.tp_order.price={}, pos_size={}, last_price={}, self.trailed_price={}, self.ttp_price={}".format(
                self.oco_context, self.tradeid, self.tp_order.ref, self.tp_order.size, self.tp_order.price, pos_size, last_price, self.tp_trailed_price, self.ttp_price))

    def cancel_sl_order(self):
        if self.is_sl_mode_activated() and self.sl_order:
            self.strategy.cancel(self.sl_order)
            self.strategy.log("Cancelled the current {} order: self.sl_order.ref={}, self.oco_context={}".format(self.get_sl_type_str(), self.sl_order.ref, self.oco_context))
            self.sl_order = None
            self.oco_context.set_sl_order(None)

    def cancel_tp_order(self):
        if self.is_tp_mode_activated() and self.tp_order:
            self.strategy.cancel(self.tp_order)
            self.strategy.log("Cancelled the current {} order: self.tp_order.ref={}, self.oco_context={}".format(self.get_tp_type_str(), self.tp_order.ref, self.oco_context))
            self.tp_order = None
            self.oco_context.set_tp_order(None)

    def is_tsl_move_pending(self, last_price, is_long):
        return self.is_tsl_enabled and self.is_sl_activated and self.is_allow_trailing_move(last_price, self.sl_trailed_price) and \
               (is_long and last_price > self.sl_trailed_price or not is_long and last_price < self.sl_trailed_price)

    def is_ttp_move_pending(self, last_price, is_long):
        return self.is_ttp_activated and self.is_allow_trailing_move(last_price, self.tp_trailed_price) and \
               (is_long and last_price > self.tp_trailed_price or not is_long and last_price < self.tp_trailed_price)

    def resubmit_oco_order(self, old_oco_order, is_long):
        if old_oco_order and old_oco_order.ref:
            if self.oco_context.is_sl_order(old_oco_order):
                self.strategy.log("Resubmitting the OCO (SL) order: old_oco_order.ref={}".format(old_oco_order.ref))
                self.sl_oco_resubmit_order(old_oco_order, is_long)
            if self.oco_context.is_tp_order(old_oco_order):
                self.strategy.log("Resubmitting the OCO (TP) order: old_oco_order.ref={}".format(old_oco_order.ref))
                self.tp_oco_resubmit_order(old_oco_order, is_long)

    def move_tsl(self, last_price, is_long):
        self.strategy.log("SLTPManager.move_tsl() - Begin:")
        sl_size = self.sl_order.size
        old_sl_trailed_price = self.sl_trailed_price
        old_sl_price = self.sl_price
        self.sl_trailed_price = last_price
        self.sl_price = self.get_sl_price(last_price, self.strategy.p.sl, is_long)
        self.strategy.log("Moving TRAILING STOP-LOSS targets: self.oco_context={}, self.trailed_price={} -> {}, self.sl_price={} -> {}, last_price={}, sl_size={}, is_long={}".format(
            self.oco_context, old_sl_trailed_price, self.sl_trailed_price, old_sl_price, self.sl_price, last_price, sl_size, is_long))
        self.cancel_sl_order()
        self.resubmit_oco_order(self.oco_context.get_tp_order(), is_long)
        self.submit_new_sl_order(is_long, self.tradeid, sl_size, self.sl_price)
        self.strategy_analyzers.ta.update_moved_tsl_counts_data(self.is_tsl_enabled)

    def move_ttp(self, last_price, is_long):
        self.strategy.log("SLTPManager.move_ttp() - Begin:")
        ttp_size = self.tp_order.size
        old_tp_trailed_price = self.tp_trailed_price
        old_ttp_price = self.ttp_price
        self.tp_trailed_price = last_price
        self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
        self.strategy.log("Moving TRAILING TAKE-PROFIT targets: self.oco_context={}, self.trailed_price={} -> {}, self.ttp_price={} -> {}, last_price={}, ttp_size={}, is_long={}".format(
            self.oco_context, old_tp_trailed_price, self.tp_trailed_price, old_ttp_price, self.ttp_price, last_price, ttp_size, is_long))
        self.cancel_tp_order()
        self.resubmit_oco_order(self.oco_context.get_sl_order(), is_long)
        self.submit_new_ttp_order(is_long, self.tradeid, ttp_size, self.ttp_price)
        self.strategy_analyzers.ta.update_moved_ttp_counts_data(self.is_ttp_enabled)

    def move_tsl_ttp(self, last_price, is_long):
        self.strategy.log("SLTPManager.move_tsl_ttp() - Begin:")
        sl_size = self.sl_order.size
        old_sl_trailed_price = self.sl_trailed_price
        old_sl_price = self.sl_price
        self.sl_trailed_price = last_price
        self.sl_price = self.get_sl_price(last_price, self.strategy.p.sl, is_long)
        self.strategy.log("Moving TRAILING STOP-LOSS targets: self.oco_context={}, self.trailed_price={} -> {}, self.sl_price={} -> {}, last_price={}, sl_size={}, is_long={}".format(
            self.oco_context, old_sl_trailed_price, self.sl_trailed_price, old_sl_price, self.sl_price, last_price, sl_size, is_long))
        self.cancel_sl_order()
        self.submit_new_sl_order(is_long, self.tradeid, sl_size, self.sl_price)
        self.strategy_analyzers.ta.update_moved_tsl_counts_data(self.is_tsl_enabled)

        ttp_size = self.tp_order.size
        old_tp_trailed_price = self.tp_trailed_price
        old_ttp_price = self.ttp_price
        self.tp_trailed_price = last_price
        self.ttp_price = self.get_ttp_price(last_price, self.strategy.p.ttpdist, is_long)
        self.strategy.log("Moving TRAILING TAKE-PROFIT targets: self.oco_context={}, self.trailed_price={} -> {}, self.ttp_price={} -> {}, last_price={}, ttp_size={}, is_long={}".format(
            self.oco_context, old_tp_trailed_price, self.tp_trailed_price, old_ttp_price, self.ttp_price, last_price, ttp_size, is_long))
        self.submit_new_ttp_order(is_long, self.tradeid, ttp_size, self.ttp_price)
        self.strategy_analyzers.ta.update_moved_ttp_counts_data(self.is_ttp_enabled)

    def move_targets(self):
        if self.is_tsl_enabled or self.is_ttp_enabled:
            is_long = self.strategy.is_long_position()
            last_price = self.strategy.data.close[0]
            tsl_move_pending = self.is_tsl_move_pending(last_price, is_long)
            ttp_move_pending = self.is_ttp_move_pending(last_price, is_long)
            self.strategy.log("Move trailing targets flags: tsl_move_pending={}, ttp_move_pending={}".format(tsl_move_pending, ttp_move_pending))
            if tsl_move_pending and not ttp_move_pending:
                self.move_tsl(last_price, is_long)
            if not tsl_move_pending and ttp_move_pending:
                self.move_ttp(last_price, is_long)
            if tsl_move_pending and ttp_move_pending:
                self.move_tsl_ttp(last_price, is_long)

    def sl_on_next(self):
        if not self.is_sl_enabled and not self.is_tsl_enabled or self.strategy.is_position_closed() or not self.is_sl_activated:
            return False

    def tp_on_next(self):
        if not self.is_tp_enabled and not self.is_ttp_enabled or self.strategy.is_position_closed() or not self.is_tp_activated:
            return False

        is_long = self.strategy.is_long_position()
        last_price = self.data.close[0]
        if self.is_ttp_enabled:
            if self.is_tp_activated and not self.is_ttp_activated:
                if self.is_tp_reached(self.tp_price, last_price, is_long):
                    pos_size = self.strategy.position.size
                    self.strategy.log("Price has reached TAKE-PROFIT target and activating TRAILING TAKE-PROFIT mode: self.tp_price={}, pos_size={}, last_price={}, is_long={}".format(
                        self.tp_price, pos_size, last_price, is_long))
                    self.activate_ttp(self.tradeid, pos_size, last_price, is_long)
                    return True

    def handle_order_completed(self, order):
        if order.status == order.Completed and self.sl_order and self.sl_order.ref == order.ref:
            self.strategy.log('SLTPManager.handle_order_completed(): order.ref={}, status={}'.format(order.ref, order.getstatusname()))
            self.strategy.log("The {} order has been triggered and COMPLETED: self.oco_context={}, self.sl_order.ref={}, self.trailed_price={}, self.sl_price={}, order.price={}, order.size={}".format(
                self.get_sl_type_str(), self.oco_context, self.sl_order.ref, self.sl_trailed_price, self.sl_price, order.price, order.size))
            self.sl_deactivate()
            self.tp_deactivate()
            self.strategy_analyzers.ta.update_sl_counts_data(self.is_tsl_enabled)
            return True

        if order.status == order.Completed and (self.tp_order and self.tp_order.ref == order.ref):
            self.strategy.log('SLTPManager.handle_order_completed(): order.ref={}, status={}'.format(order.ref, order.getstatusname()))
            self.strategy.log("The {} order has been triggered and COMPLETED: self.oco_context={}, self.tp_order.ref={}, self.trailed_price={}, self.tp_price={}, self.ttp_price={}, order.price={}, order.size={}".format(
                self.get_tp_type_str(), self.oco_context, self.tp_order.ref, self.tp_trailed_price, self.tp_price, self.ttp_price, order.price, order.size))
            self.sl_deactivate()
            self.tp_deactivate()
            self.strategy_analyzers.ta.update_tp_counts_data(self.is_ttp_enabled)
            return True
        return False

    def sl_deactivate(self):
        if self.is_sl_enabled and self.is_sl_mode_activated():
            sl_order_ref = self.sl_order.ref if self.sl_order else None
            self.strategy.log('SLTPManager.sl_deactivate() - {} will be deactivated, self.oco_context={}, self.sl_order.ref={}'.format(self.get_sl_type_str(), self.oco_context, sl_order_ref))
            self.cancel_sl_order()
            self.oco_context.reset()
            self.is_sl_activated = False
            self.sl_order = None

    def tp_deactivate(self):
        if self.is_tp_enabled and self.is_tp_mode_activated():
            tp_order_ref = self.tp_order.ref if self.tp_order else None
            self.strategy.log('TakeProfitManager.tp_deactivate() - {} will be deactivated, self.oco_context={}, self.tp_order.ref={}'.format(self.get_tp_type_str(), self.oco_context, tp_order_ref))
            self.cancel_tp_order()
            self.oco_context.reset()
            self.is_tp_activated = False
            self.is_ttp_activated = False
            self.tp_order = None

    def is_sl_reached(self, sl_price, last_price, is_long):
        result = False
        if is_long and last_price < sl_price or not is_long and last_price > sl_price:
            result = True
        return result

    def is_tp_reached(self, tp_price, last_price, is_long):
        result = False
        if is_long and last_price > tp_price or not is_long and last_price < tp_price:
            result = True
        return result

    def is_ttp_reached(self, tp_price, last_price, is_long):
        result = False
        if is_long and last_price < tp_price or not is_long and last_price > tp_price:
            result = True
        return result

    def get_sl_price(self, base_price, sl_dist_pct, is_long):
        if is_long:
            return base_price * (1 - sl_dist_pct / 100.0)
        else:
            return base_price * (1 + sl_dist_pct / 100.0)

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

    def is_allow_trailing_move(self, price1, price2):
        if self.get_price_move_delta_pct(price1, price2) >= MOVE_TRAILING_PRICE_DELTA_THRESHOLD_PCT:
            return True
        else:
            return False

    def get_price_move_delta_pct(self, price1, price2):
        return abs(100 * (price1 - price2) / price2)

