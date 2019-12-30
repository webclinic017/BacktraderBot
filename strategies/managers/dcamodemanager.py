import backtrader as bt


class DcaModeManager(object):

    def __init__(self, strategy, strategyprocessor, oco_context):
        self.strategy = strategy
        self.strategyprocessor = strategyprocessor
        self.oco_context = oco_context
        self.data = strategy.data
        self.strategy_analyzers = strategy.analyzers

        self.is_dca_mode_enabled = self.strategy.p.numdca is not None and self.strategy.p.numdca > 0 and self.strategy.p.dcainterval is not None and self.strategy.p.dcainterval > 0
        self.is_dca_activated = False

        self.is_long_signal = None
        self.long_orders = [None] * self.strategy.p.numdca
        self.short_orders = [None] * self.strategy.p.numdca
        self.num_dca_orders_triggered = 0

    def is_dca_mode_activated(self):
        return self.is_dca_activated

    def get_order_idx(self, order):
        for idx in range(0,  self.strategy.p.numdca):
            order_long = self.long_orders[idx]
            order_short = self.short_orders[idx]
            if order_long and order_long.ref == order.ref or order_short and order_short.ref == order.ref:
                return idx
        return None

    def get_dca_orders_count(self):
        result = 0
        for idx in range(0,  self.strategy.p.numdca):
            order_long = self.long_orders[idx]
            order_short = self.short_orders[idx]
            if order_long:
                result += 1
            if order_short:
                result += 1
        return result

    def store_order(self, is_long, idx, o):
        if is_long is True:
            self.long_orders[idx] = o
        else:
            self.short_orders[idx] = o

    def update_order(self, is_long, order):
        orders_list = self.long_orders if is_long is True else self.short_orders
        for i in range(0,  self.strategy.p.numdca):
            table_order = orders_list[i]
            if table_order and table_order.ref == order.ref:
                orders_list[i] = order

    def check_order_is_stored(self, is_long, order):
        orders_list = self.long_orders if is_long else self.short_orders
        for i in range(0,  self.strategy.p.numdca):
            table_order = orders_list[i]
            if table_order and table_order.ref == order.ref:
                return True
        return False

    def get_desired_order_size(self, is_long):
        full_size = self.strategyprocessor.get_order_size(self.strategy.data, is_long)
        number_of_orders = self.strategy.p.numdca + 1  # 1 base order + number of DCA orders
        return round(full_size / (1.0 * number_of_orders), 8)

    def get_desired_order_price(self, is_long, idx, last_price):
        price_bracket_pct = (idx + 1) * self.strategy.p.dcainterval / 100.0
        if is_long:
            return round(last_price * (1 - price_bracket_pct), 8)
        else:
            return round(last_price * (1 + price_bracket_pct), 8)

    def get_oco_order(self):
        if self.oco_context.get_sl_order():
            return self.oco_context.get_sl_order()
        elif self.oco_context.get_tp_order():
            return self.oco_context.get_tp_order()
        else:
            return None

    def submit_new_dca_order(self, is_long, tradeid, dca_size, dca_price):
        oco_order = self.get_oco_order()
        if is_long:
            dca_order = self.strategy.generic_buy(tradeid=tradeid, size=dca_size, price=dca_price, exectype=bt.Order.Limit, oco=oco_order)
            self.strategy.log('Submitted a new DCA-MODE order (BUY LIMIT): tradeid={}, dca_size={}, dca_price={}, dca_order.ref={}, dca_order.size={}, dca_order.price={}, dca_order.side={}, oco_order.ref={}'.format(
                tradeid, dca_size, dca_price, dca_order.ref, dca_order.size, dca_order.price, dca_order.ordtypename(), oco_order.ref))
        else:
            dca_order = self.strategy.generic_sell(tradeid=tradeid, size=dca_size, price=dca_price, exectype=bt.Order.Limit, oco=oco_order)
            self.strategy.log('Submitted a new DCA-MODE order (SELL LIMIT): tradeid={}, dca_size={}, dca_price={}, dca_order.ref={}, dca_order.size={}, dca_order.price={}, dca_order.side={}, oco_order.ref={}'.format(
                tradeid, dca_size, dca_price, dca_order.ref, dca_order.size, dca_order.price, dca_order.ordtypename(), oco_order.ref))
        return dca_order

    def submit_dca_orders(self, is_long, last_price, tradeid):
        for idx in range(0, self.strategy.p.numdca):
            order_size = self.get_desired_order_size(is_long)
            order_price = self.get_desired_order_price(is_long, idx, last_price)
            new_order = self.submit_new_dca_order(is_long, tradeid, order_size, order_price)
            if new_order:
                self.strategy.log('submit_dca_orders(): Submitted the new {} order, i={}, new_order.ref={}, is_long={}, last_price={}'.format("LONG" if is_long else "SHORT", idx, new_order.ref, is_long, last_price))
                self.store_order(is_long, idx, new_order)

    def get_order_refs_str(self, orders):
        result = ""
        for i in range(0, self.strategy.p.numdca):
            o = orders[i]
            if o and o.ref and o.status:
                result += "[{}]:{}={}({})".format(i, o.ref, o.getstatusname(), o.price)
            else:
                result += "[{}]:None".format(i)
            if i < self.strategy.p.numdca - 1:
                result += ","
        return result

    def activate_dca_mode(self, tradeid, last_price, is_long):
        if self.is_dca_mode_enabled and not self.is_dca_mode_activated():
            self.is_long_signal = is_long

            self.submit_dca_orders(is_long, last_price, tradeid)

            self.num_dca_orders_triggered = 0
            self.is_dca_activated = True

            self.strategy.log("Activated DCA-MODE for self.tradeid={}, last_price={}, is_long={}".format(tradeid, last_price, is_long))

    def cancel_order(self, order):
        if self.is_dca_mode_activated() and order:
            self.strategy.cancel(order)
            self.strategy.log("Cancelled the DCA order: order.ref={}".format(order.ref))

    def cancel_all_dca_orders(self):
        for i in range(0, self.strategy.p.numdca):
            long_order = self.long_orders[i]
            short_order = self.short_orders[i]

            if long_order and long_order.status in [bt.Order.Submitted, bt.Order.Accepted]:
                self.cancel_order(long_order)
            if short_order and short_order.status in [bt.Order.Submitted, bt.Order.Accepted]:
                self.cancel_order(short_order)

            self.store_order(True, i, None)
            self.store_order(False, i, None)

    def dca_on_next(self):
        if not self.is_dca_mode_enabled or self.strategy.is_position_closed() or not self.is_dca_mode_activated():
            return False

    def get_curr_position_size(self, order):
        if order and order.isbuy():
            return 1
        elif order and order.issell():
            return -1
        else:
            return 0

    def resubmit_dca_orders(self, is_long, tradeid):
        self.strategy.log("Resubmitting all existing DCA orders:")
        for idx in range(0, self.strategy.p.numdca):
            old_dca_order = self.long_orders[idx] if is_long else self.short_orders[idx]
            if old_dca_order and old_dca_order.ref:
                new_order = self.submit_new_dca_order(is_long, tradeid, old_dca_order.size, old_dca_order.price)
                if new_order:
                    self.strategy.log('submit_dca_orders(): Resubmitted the DCA {} order, i={}, old_dca_order.ref={}, new_order.ref={}, is_long={}'.format("LONG" if is_long else "SHORT", idx, old_dca_order.ref, new_order.ref, is_long))
                    self.store_order(is_long, idx, new_order)

    def handle_order_completed(self, order):
        if self.strategy.is_beyond_daterange():
            return False

        if self.is_dca_mode_enabled and self.is_dca_mode_activated() and order.status == order.Completed and self.check_order_is_stored(self.is_long_signal, order):
            self.strategy.log('DcaModeManager.handle_order_completed(): order.ref={}, order.status={}, order.tradeid={}, order.price={}, order.size={}, order.side={}'.format(
                order.ref, order.getstatusname(), order.tradeid, order.price, order.size, order.ordtypename(), self.num_dca_orders_triggered))
            self.strategy.curr_position = self.get_curr_position_size(order)
            self.strategy.position_avg_price = self.strategy.position.price
            idx = self.get_order_idx(order)
            self.store_order(self.is_long_signal, idx, None)
            self.strategy_analyzers.ta.update_dca_triggered_counts_data()
            self.num_dca_orders_triggered += 1

            self.strategy.deactivate_trade_managers()
            self.strategy.activate_trade_managers(self.strategy.curtradeid, self.strategy.position.price, self.strategy.position.size, self.is_long_signal)
            dca_orders_count = self.get_dca_orders_count()
            if dca_orders_count > 0:
                self.strategy.log("The number of active orders={}. All non-closed DCA-MODE orders will be resubmitted.".format(dca_orders_count))
                self.resubmit_dca_orders(self.is_long_signal, self.strategy.curtradeid)

            self.strategy.log("The DCA-MODE order has been triggered and COMPLETED: self.strategy.curr_position={}, self.strategy.position_avg_price={}, self.num_dca_orders_triggered={}, self.get_dca_orders_count()={}".format(
                self.strategy.curr_position, self.strategy.position_avg_price, self.num_dca_orders_triggered, self.get_dca_orders_count()))
            return True
        return False

    def dca_mode_deactivate(self):
        if self.is_dca_mode_enabled and self.is_dca_mode_activated():
            self.strategy.log('DcaModeManager.dca_mode_deactivate() - DCA-MODE will be deactivated')
            self.cancel_all_dca_orders()
            self.is_dca_activated = False
            self.is_long_signal = None
            self.num_dca_orders_triggered = 0
            self.dca_sl_timeout_start_bar = -1

    def log_state(self):
        if self.is_dca_mode_enabled:
            self.strategy.log('DcaModeManager.num_dca_orders_triggered = {}'.format(self.num_dca_orders_triggered))
            self.strategy.log('DcaModeManager.long_orders = [{}]'.format(self.get_order_refs_str(self.long_orders)))
            self.strategy.log('DcaModeManager.short_orders = [{}]'.format(self.get_order_refs_str(self.short_orders)))
