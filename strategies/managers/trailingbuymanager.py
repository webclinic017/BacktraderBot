import backtrader as bt

MOVE_TRAILING_PRICE_DELTA_THRESHOLD_PCT = 0.1


class TrailingBuyManager(object):

    def __init__(self, strategy):
        self.strategy = strategy
        self.data = strategy.data
        self.strategy_analyzers = strategy.analyzers

        self.is_tb_enabled = self.strategy.p.tbdist is not None and self.strategy.p.tbdist > 0
        self.is_tb_activated = False

        self.is_long_signal = None
        self.tradeid = None
        self.tb_order = None
        self.tb_price = None
        self.tb_trailed_price = None

    def is_tb_mode_activated(self):
        return self.is_tb_activated

    def submit_new_tb_order(self, tradeid, tb_price):
        if self.is_long_signal:
            self.tb_order = self.strategy.generic_buy(tradeid=tradeid, price=tb_price, exectype=bt.Order.Stop)
            self.strategy.log('Submitted a new TRAILING-BUY order (BUY STOP MARKET): tradeid={}, tb_price={}, tb_order.ref={}, tb_order.size={}, tb_order.price={}, tb_order.side={}'.format(
                tradeid, tb_price, self.tb_order.ref, self.tb_order.size, self.tb_order.price, self.tb_order.ordtypename()))
        else:
            self.tb_order = self.strategy.generic_sell(tradeid=tradeid, price=tb_price, exectype=bt.Order.Stop)
            self.strategy.log('Submitted a new TRAILING-BUY order (SELL STOP MARKET): tradeid={}, tb_price={}, tb_order.ref={}, tb_order.size={}, tb_order.price={}, tb_order.side={}'.format(
                tradeid, tb_price, self.tb_order.ref, self.tb_order.size, self.tb_order.price, self.tb_order.ordtypename()))

    def activate_tb(self, tradeid, last_price, is_long):
        if self.is_tb_enabled and not self.is_tb_mode_activated():
            self.is_long_signal = is_long
            self.tradeid = tradeid
            self.tb_price = self.get_tb_price(last_price, self.strategy.p.tbdist)
            self.tb_trailed_price = last_price
            self.submit_new_tb_order(self.tradeid, self.tb_price)
            self.is_tb_activated = True
            self.strategy.log("Activated TRAILING-BUY mode for self.tradeid={}, self.tb_order.ref={}, self.tb_order.size={}, self.tb_order.price={}, last_price={}, self.tb_price={}, self.tb_trailed_price={}".format(
               self.tradeid, self.tb_order.ref, self.tb_order.size, self.tb_order.price, last_price, self.tb_price, self.tb_trailed_price))

    def cancel_tb_order(self):
        if self.is_tb_mode_activated() and self.tb_order:
            self.strategy.cancel(self.tb_order)
            self.strategy.log("Cancelled the current TRAILING-BUY order: self.tb_order.ref={}".format(self.tb_order.ref))
            self.tb_order = None

    def is_tb_move_pending(self, last_price):
        self.strategy.log("is_tb_move_pending(): last_price={}, self.is_long_signal={}".format(last_price, self.is_long_signal))
        return self.is_tb_mode_activated() and self.tb_order and self.strategy.is_order_accepted_in_broker(self.tb_order) and \
               self.is_allow_trailing_move(last_price, self.tb_trailed_price) and (self.is_long_signal and last_price < self.tb_trailed_price or not self.is_long_signal and last_price > self.tb_trailed_price)

    def move_tb(self, last_price):
        self.strategy.log("TrailingBuyManager.move_tb() - Begin:")
        tb_size = self.tb_order.size
        old_tb_trailed_price = self.tb_trailed_price
        old_tb_price = self.tb_price
        self.tb_trailed_price = last_price
        self.tb_price = self.get_tb_price(last_price, self.strategy.p.tbdist)
        self.strategy.log("Moving TRAILING-BUY target: self.tb_trailed_price={} -> {}, self.tb_price={} -> {}, last_price={}, tb_size={}, self.is_long_signal={}".format(
            old_tb_trailed_price, self.tb_trailed_price, old_tb_price, self.tb_price, last_price, tb_size, self.is_long_signal))
        self.cancel_tb_order()
        self.submit_new_tb_order(self.tradeid, self.tb_price)
        self.strategy_analyzers.ta.update_moved_tb_counts_data()

    def move_targets(self):
        if self.is_tb_enabled and self.is_tb_mode_activated():
            last_price = self.strategy.data.close[0]
            tb_move_pending = self.is_tb_move_pending(last_price)
            self.strategy.log("Move TRAILING-BUY flag: tb_move_pending={}".format(tb_move_pending))
            if tb_move_pending:
                self.move_tb(last_price)

    def tb_on_next(self):
        if not self.is_tb_enabled or self.strategy.is_position_closed() or not self.is_tb_activated:
            return False

    def get_position_size(self, order):
        if order.isbuy():
            return 1
        elif order.issell():
            return -1
        else:
            return 0

    def handle_order_completed(self, order):
        if self.is_tb_enabled and self.is_tb_mode_activated() and order.status == order.Completed and self.tb_order and self.tb_order.ref == order.ref:
            self.strategy.log('TrailingBuyManager.handle_order_completed(): order.ref={}, status={}'.format(order.ref, order.getstatusname()))
            self.strategy.log("The TRAILING-BUY order has been triggered and COMPLETED: self.tb_order.ref={}, self.tb_price={}, self.tb_trailed_price={}, order.price={}, order.size={}".format(
                self.tb_order.ref, self.tb_price, self.tb_trailed_price, order.price, order.size))
            self.strategy.curr_position = self.get_position_size(order)
            self.strategy.position_avg_price = order.price
            self.tb_order = None
            self.tb_deactivate()
            self.strategy_analyzers.ta.update_tb_counts_data()
            self.strategy.log('!!! AFTER - TRAILING-BUY MODE - OPEN POSITION {} !!!, self.curr_position={}, cash={}'.format(
                self.strategy.get_side_str(self.strategy.is_long_position()), self.strategy.curr_position, self.strategy.broker.getcash()))
            return True
        return False

    def tb_deactivate(self):
        if self.is_tb_enabled and self.is_tb_mode_activated():
            tb_order_ref = self.tb_order.ref if self.tb_order else None
            self.strategy.log('TrailingBuyManager.tb_deactivate() - TRAILING-BUY will be deactivated, self.tb_order.ref={}'.format(tb_order_ref))
            self.cancel_tb_order()
            self.is_tb_activated = False
            self.is_long_signal = None
            self.tradeid = None
            self.tb_order = None
            self.tb_price = None
            self.tb_trailed_price = None

    def get_tb_price(self, base_price, tb_dist_pct):
        if self.is_long_signal:
            return round(base_price * (1 + tb_dist_pct / 100.0), 8)
        else:
            return round(base_price * (1 - tb_dist_pct / 100.0), 8)

    def is_allow_trailing_move(self, price1, price2):
        return self.get_price_move_delta_pct(price1, price2) >= MOVE_TRAILING_PRICE_DELTA_THRESHOLD_PCT

    def get_price_move_delta_pct(self, price1, price2):
        return abs(100 * (price1 - price2) / price2)

    def log_state(self):
        if self.is_tb_enabled:
            self.strategy.log('TrailingBuyManager.tb_price = {}'.format(self.tb_price))
            self.strategy.log('TrailingBuyManager.tb_trailed_price = {}'.format(self.tb_trailed_price))
