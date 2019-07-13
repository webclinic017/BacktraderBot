from datetime import datetime
import pytz
import backtrader as bt
import itertools
import re

STATUS_BEGIN, STATUS_INPROGRESS, STATUS_CLOSED = range(3)


class S012_GridMarketMakerStrategy(bt.Strategy):
    '''
    This is an implementation of a strategy from TradingView - S012 Grid Market Maker v1.0 Strategy.
    '''
    params = (
        ("debug", False),
        ("startcash", 1500000),
        ("order_pairs", 6),
        ("order_start_size", 10),
        ("order_step_size", 1),
        ("interval_pct", 0.002),
        ("min_spread_pct", 0.004),
        ("relist_interval_pct", 0.004),
        ("min_position", -75),
        ("max_position", 75),
        ("stop_quoting_if_inside_loss_range", True),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 1),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.long_orders = [None] * self.p.order_pairs
        self.short_orders = [None] * self.p.order_pairs
        self.status = STATUS_BEGIN

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle(range(1, 10000000))

        self.curtrade = None

    def log(self, txt, send_telegram_flag=False):
        if self.p.debug:
            dt = self.data.datetime.datetime()
            print('%s  %s' % (dt, txt))

    def get_data_symbol(self, data):
        data_symbol_regex = "marketdata\/.*\/(.*)\/.*\/.*"
        data_symbol = re.search(data_symbol_regex, data.p.dataname)
        return data_symbol.group(1)

    def store_order_in_table(self, is_long, idx, o):
        if is_long is True:
            self.long_orders[idx] = o
        else:
            self.short_orders[idx] = o

    def update_order_in_table(self, is_long, order):
        orders_list = self.long_orders if is_long is True else self.short_orders
        for i in range(0, self.p.order_pairs):
            table_order = orders_list[i]
            if table_order is not None and table_order.ref == order.ref:
                orders_list[i] = order

    def get_desired_order_size(self, idx):
        return round(self.p.order_start_size + idx * self.p.order_step_size, 8)

    def get_desired_order_price(self, is_long, idx):
        price_bracket_pct = self.p.min_spread_pct / 2 + idx * self.p.interval_pct
        if is_long is True:
            return round(self.data.close[0] * (1 - price_bracket_pct))
        else:
            return round(self.data.close[0] * (1 + price_bracket_pct))

    def is_order_placement_allowed(self, is_long, order_price):
        self.log("is_order_placement_allowed(): BEGIN")

        result = True
        position_qty = self.position.size
        is_order_buy_side = is_long

        if self.p.stop_quoting_if_inside_loss_range is False or position_qty == 0 or self.curtrade is None:
            result = True
        else:
            position_avg_price = self.curtrade.price
            if position_qty > 0:
                if is_order_buy_side is True:
                    result = True
                else:
                    if order_price >= position_avg_price:
                        result = True
                    else:
                        result = False
            else:
                if is_order_buy_side is False:
                    result = True
                else:
                    if order_price <= position_avg_price:
                        result = True
                    else:
                        result = False

        self.log("is_order_placement_allowed(): is_long={}, order_price={}, result={}".format(is_long, order_price, result))
        return result

    def submit_new_order(self, is_long, idx):
        order_size = self.get_desired_order_size(idx)
        long_order_price = self.get_desired_order_price(True, idx)
        short_order_price = self.get_desired_order_price(False, idx)
        if is_long is True:
            if self.is_order_placement_allowed(True, long_order_price) is False:
                return None
            self.log('submit_order(): Submitted a new LONG order, order_size={}, self.data.close[0]={}, long_order_price={}'.format(order_size, self.data.close[0], long_order_price))
            return self.buy(size=order_size, price=long_order_price, exectype=bt.Order.Limit)
        else:
            if self.is_order_placement_allowed(False, short_order_price) is False:
                return None
            self.log('submit_order(): Submitted a new SHORT order, order_size={}, self.data.close[0]={}, long_order_price={}'.format(order_size, self.data.close[0], short_order_price))
            return self.sell(size=order_size, price=short_order_price, exectype=bt.Order.Limit)

    def converge_order(self, order, is_long, idx):
        self.log('converge_order(): BEGIN order.ref={}, is_long={}, idx={}'.format(order.ref if order is not None else None, is_long, idx))
        if is_long is True and self.position.size >= self.p.max_position or is_long is False and self.position.size <= self.p.min_position:
            if order is None:
                self.log('converge_order(): self.position.size({}) has exceeded the min/max position size. Skipped quoting the {} side.'.format(self.position.size, "LONG" if self.position.size > 0 else "SHORT"))
                self.store_order_in_table(is_long, idx, None)
                return
            elif order is not None and order.status == bt.Order.Completed:
                self.log('converge_order(): self.position.size({}) has exceeded the min/max position size. Stopped quoting the {} side and skipped submitting a new order for completed order ref={}.'.format(self.position.size, "LONG" if self.position.size > 0 else "SHORT", order.ref))
                self.store_order_in_table(is_long, idx, None)
                return
            elif order is not None and order.status == bt.Order.Accepted:
                self.log('converge_order(): self.position.size({}) has exceeded the min/max position size. Stopped quoting the {} side and cancelling existing order ref={}.'.format(self.position.size, "LONG" if self.position.size > 0 else "SHORT", order.ref))
                self.cancel(order)
                self.store_order_in_table(is_long, idx, None)
                return
            elif order is not None and order.status == bt.Order.Canceled:
                self.log('converge_order(): self.position.size({}) has exceeded the min/max position size. Skipping canceled order {}, is_long={}, idx={}'.format(self.position.size, order.ref, is_long, idx))
                self.store_order_in_table(is_long, idx, None)
        elif order is None or order.status in [bt.Order.Completed, bt.Order.Canceled]:
            new_order = self.submit_new_order(is_long, idx)
            if new_order is not None:
                self.log('converge_orders(): Submitted the new {} order, i={}, new_order.ref={}'.format("LONG" if is_long else "SHORT", idx, new_order.ref))
                self.store_order_in_table(is_long, idx, new_order)
        elif order.status == bt.Order.Accepted:
            desired_order_price = self.get_desired_order_price(is_long, idx)
            desired_to_curr_price_diff_pct = abs((desired_order_price - order.price) / order.price)
            if desired_to_curr_price_diff_pct > self.p.relist_interval_pct:
                self.log('converge_order(): the existing order ref={} price={} has deviated from desired price={} for more than allowed relisting interval={}. The order will be cancelled and new order would be submitted.'.format(order.ref, order.price, desired_order_price, self.p.relist_interval_pct))
                self.cancel(order)
                new_order = self.submit_new_order(is_long, idx)
                if new_order is not None:
                    self.log('converge_orders(): Instead of the previous order ref={} submitted the new {} order, i={}, new_order.ref={}'.format(order.ref, "LONG" if is_long else "SHORT", idx, new_order.ref))
                    self.store_order_in_table(is_long, idx, new_order)

    def converge_orders(self):
        for i in range(0, self.p.order_pairs):
            long_order = self.long_orders[i]
            short_order = self.short_orders[i]
            self.converge_order(long_order, True, i)
            self.converge_order(short_order, False, i)

    def cancel_all_orders(self):
        for i in range(0, self.p.order_pairs):
            long_order = self.long_orders[i]
            short_order = self.short_orders[i]

            if long_order is not None and long_order.status in [bt.Order.Submitted, bt.Order.Accepted]:
                self.cancel(long_order)
            if short_order is not None and short_order.status in [bt.Order.Submitted, bt.Order.Accepted]:
                self.cancel(short_order)

            self.store_order_in_table(True, i, None)
            self.store_order_in_table(False, i, None)

    def next(self):
        self.curtrade = self._trades[self.data][0][-1] if len(self._trades[self.data][0]) > 0 else None

        self.printdebuginfonextinner()

        # Trading
        self.fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        self.todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59, 59)
        self.currdt = self.data.datetime.datetime()

        self.gmt3_tz = pytz.timezone('Etc/GMT-3')
        self.fromdt = pytz.utc.localize(self.fromdt)
        self.todt = pytz.utc.localize(self.todt)
        self.currdt = self.gmt3_tz.localize(self.currdt, is_dst=True)

        if self.currdt > self.fromdt and self.currdt < self.todt:
            if self.status == STATUS_BEGIN:
                self.converge_orders()
                self.status = STATUS_INPROGRESS

            if self.status == STATUS_INPROGRESS:
                self.converge_orders()

        if self.currdt > self.todt:
            if self.status != STATUS_CLOSED:
                self.log('!!! Time passed beyond date range: Closing opened orders and positions and exiting.')
                self.cancel_all_orders()
                self.close()
                self.status = STATUS_CLOSED

    def notify_order(self, order):
        self.log('notify_order() - order.ref={}, status={}, order.size={}, order.price={}, broker.cash={}, self.position.size = {}'.format(order.ref, order.getstatusname(), order.size, order.price, round(self.broker.getcash(),2), self.position.size))
        if order.status in [bt.Order.Created, bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed and self.status != STATUS_CLOSED:
            if order.isbuy():
                self.update_order_in_table(True, order)
                buytxt = 'BUY COMPLETE, symbol={}, order.ref={}, order.size={}, {} - at {}'.format(self.get_data_symbol(self.data), order.ref, order.size, order.executed.price, bt.num2date(order.executed.dt))
                self.log(buytxt, True)
            else:
                self.update_order_in_table(False, order)
                selltxt = 'SELL COMPLETE, symbol={}, order.ref={}, order.size={}, {} - at {}'.format(self.get_data_symbol(self.data), order.ref, order.size, order.executed.price, bt.num2date(order.executed.dt))
                self.log(selltxt, True)
            self.converge_orders()
        elif order.status == order.Canceled:
            self.log('Order has been Cancelled: Symbol {}, Status {}, order.ref={}'.format(self.get_data_symbol(self.data), order.Status[order.status], order.ref), True)
        elif order.status in [order.Expired, order.Rejected]:
            self.log('Order has been Expired/Rejected: Symbol {}, Status {}, order.ref={}'.format(self.get_data_symbol(self.data), order.Status[order.status], order.ref), True)
            self.curr_position = 0
        elif order.status == order.Margin:
            self.log('notify_order() - ********** MARGIN CALL!! SKIPPING!! **********', True)
            self.env.runstop()


    def notify_trade(self, trade):
        self.log('!!! BEGIN notify_trade() - id(self)={}, traderef={}, self.broker.getcash()={}'.format(id(self), trade.ref, self.broker.getcash()))

        if trade.justopened:
            self.log('TRADE JUST OPENED, SIZE={}, REF={}, VALUE={}, COMMISSION={}, BROKER CASH={}'.format(trade.size, trade.ref, trade.value, trade.commission, self.broker.getcash()))

        if trade.isclosed:
            self.log('---------------------------- TRADE CLOSED --------------------------')
            self.log("1: Data Name:                            {}".format(trade.data._name))
            self.log("2: Bar Num:                              {}".format(len(trade.data)))
            self.log("3: Current date:                         {}".format(self.data.datetime.date()))
            self.log('4: Status:                               Trade Complete')
            self.log('5: Ref:                                  {}'.format(trade.ref))
            self.log('6: PnL:                                  {}'.format(round(trade.pnl, 2)))
            self.log('--------------------------------------------------------------------')

    def get_order_refs_str(self, orders):
        result = ""
        for i in range(0, self.p.order_pairs):
            o = orders[i]
            if o and o.ref and o.status:
                result += "[{}]:{}={}({})".format(i, o.ref, o.getstatusname(), o.price)
            else:
                result += "[{}]:None".format(i)
            if i < self.p.order_pairs - 1:
                result += ","
        return result

    def printdebuginfonextinner(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        if self.curtrade is not None:
            self.log('self.curtrade.ref = {}'.format(self.curtrade.ref))
            self.log('Position AvgPrice = {}'.format(self.curtrade.price))
            self.log('self.curtrade.pnlcomm = {}'.format(self.curtrade.pnlcomm))
            self.log('self.curtrade.pnlcomm = {}'.format(self.curtrade.status))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.data.datetime[0] = {}'.format(self.data.datetime.datetime()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))
        self.log('self.long_orders = [{}]'.format(self.get_order_refs_str(self.long_orders)))
        self.log('self.short_orders = [{}]'.format(self.get_order_refs_str(self.short_orders)))
        self.log('self.status = {}'.format(self.status))
        self.log('--------------------------------------------------------------------')
