import backtrader as bt
from abc import abstractmethod
import itertools
from datetime import datetime
import pytz
from bot.config.bot_strategy_config import BotStrategyConfig
from strategies.managers.livetradingstrategyprocessor import LiveTradingStrategyProcessor
from strategies.managers.backtestingstrategyprocessor import BacktestingStrategyProcessor
from termcolor import colored
import re


class ParametersValidator(object):
    @classmethod
    def validate_params(cls, params):
        if not params.get("needlong") and not params.get("needshort"):
            raise ValueError("Either 'needlong' or 'needshort' parameters must be provided")
        if params.get("tslflag") and not params.get("sl"):
            raise ValueError("The 'tslflag' parameter should be provided with 'sl' parameter")
        if params.get("ttpdist") and not params.get("tp"):
            raise ValueError("The 'ttpdist' parameter cannot be provided without 'tp' parameter")
        if params.get("dcainterval") and not params.get("numdca") or not params.get("dcainterval") and params.get("numdca"):
            raise ValueError("Both 'dcainterval' and 'numdca' must be provided")
        return True


class StrategyProcessorFactory(object):
    @classmethod
    def build_strategy_processor(cls, strategy, debug):
        if strategy.islivedata():
            return LiveTradingStrategyProcessor(strategy, debug)
        else:
            return BacktestingStrategyProcessor(strategy, debug)


class GenericStrategy(bt.Strategy):

    def check_params(self):
        ParametersValidator.validate_params(vars(self.p))

    def __init__(self):
        self.curtradeid = -1
        self.curr_position = 0
        self.position_avg_price = 0
        self.tradesopen = {}
        self.tradesclosed = {}

        self.is_open_long = False
        self.is_close_long = False
        self.is_open_short = False
        self.is_close_short = False

        self.check_params()

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle(range(1, 10000000))

        self.strategyprocessor = StrategyProcessorFactory.build_strategy_processor(self, self.p.debug)

        self.is_margin_condition = False
        self.processing_status = None

    def islivedata(self):
        return self.data.islive()

    def log(self, txt, send_telegram_flag=False):
        self.strategyprocessor.log(txt, send_telegram_flag)

    def check_arr_equal(self, arr, val, last_num):
        cmp_arr = arr[len(arr) - last_num:len(arr)]
        return cmp_arr[0] == val and cmp_arr[1:] == cmp_arr[:-1]

    def _nz(self, data_arr, idx):
        if len(data_arr) < (abs(idx) + 1):
            return 0
        else:
            return data_arr[idx]

    def _nzd(self, data_arr, idx, defvalue):
        if len(data_arr) < (abs(idx) + 1):
            return defvalue
        else:
            return data_arr[idx]

    def notify_data(self, data, status, *args, **kwargs):
        return self.strategyprocessor.notify_data(data, status, args, kwargs)

    def start(self):
        if not self.islivedata():
            start_cash = self.p.startcash
        else:
            start_cash = BotStrategyConfig.get_instance().start_cash
        self.strategyprocessor.set_startcash(start_cash)

    @abstractmethod
    def calculate_signals(self):
        pass

    def get_side_str(self, is_long):
        return "LONG" if is_long else "SHORT"

    def generic_buy(self, tradeid=None, size=None, price=None, exectype=None, params=None, oco=None):
        return self.buy(tradeid=tradeid, size=size, price=price, exectype=exectype, params=params, oco=oco)

    def generic_sell(self, tradeid=None, size=None, price=None, exectype=None, params=None, oco=None):
        return self.sell(tradeid=tradeid, size=size, price=price, exectype=exectype, params=params, oco=oco)

    def generic_close(self, tradeid=None, params=None):
        return self.close(tradeid=tradeid, params=params)

    def signal_open_position(self, is_long):
        cash = self.broker.getcash()
        side_str = self.get_side_str(is_long)
        self.log('!!! BEFORE OPEN {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))
        self.curtradeid = next(self.tradeid)
        if is_long:
            base_order = self.strategyprocessor.open_long_position()
            self.curr_position = 1
        else:
            base_order = self.strategyprocessor.open_short_position()
            self.curr_position = -1
        self.position_avg_price = self.data.close[0]
        self.strategyprocessor.on_open_position_trade_managers(self.curtradeid, self.position_avg_price, base_order.size, is_long)
        self.log('!!! AFTER OPEN {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))

    def signal_close_position(self, is_long):
        cash = self.broker.getcash()
        side_str = self.get_side_str(is_long)
        self.log('!!! BEFORE CLOSE {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))
        self.strategyprocessor.close_position()
        self.curr_position = 0
        self.position_avg_price = 0
        self.strategyprocessor.notify_analyzers()
        self.strategyprocessor.on_close_position_trade_managers()
        self.log('!!! AFTER CLOSE {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def set_processing_status(self):
        if self.islivedata():
            return

        ta_analyzer = self.analyzers.ta
        if self.is_margin_condition:
            ta_analyzer.update_processing_status("Margin")
        else:
            analysis = ta_analyzer.get_analysis()
            total_open = analysis.total.open if self.exists(analysis, ['total', 'open']) else 0
            if total_open != 0:
                ta_analyzer.update_processing_status("OpenTrades")
            else:
                ta_analyzer.update_processing_status("Success")

    def execute_signals(self):
        # Trading
        self.fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        self.todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59, 59)
        self.currdt = self.data.datetime.datetime()

        self.gmt3_tz = pytz.timezone('Etc/GMT-3')
        self.fromdt = pytz.utc.localize(self.fromdt)
        self.todt = pytz.utc.localize(self.todt)
        self.currdt = self.gmt3_tz.localize(self.currdt, is_dst=True)

        #if True: #self.strategyprocessor.is_allow_signals_execution():
        if self.islivedata() or self.currdt > self.fromdt and self.currdt < self.todt:
            if self.is_short_position() and self.is_close_short is True:
                self.signal_close_position(False)

            if self.is_position_closed() and self.p.needlong is True and self.is_open_long is True:
                self.signal_open_position(True)

            if self.is_long_position() and self.is_close_long is True:
                self.signal_close_position(True)

            if self.is_position_closed() and self.p.needshort is True and self.is_open_short is True:
                self.signal_open_position(False)

        if not self.islivedata() and self.currdt > self.todt:
            self.log('!!! Time has passed beyond date range')
            if self.curr_position != 0:  # if 'curtradeid' in self:
                self.log('!!! Closing trade prematurely')
                self.signal_close_position(self.is_long_position())
            self.curr_position = 0
            self.position_avg_price = 0
            self.set_processing_status()

    @abstractmethod
    def printdebuginfo(self):
        pass

    def is_position_closed(self):
        return self.curr_position == 0

    def is_long_position(self):
        return self.curr_position > 0

    def is_short_position(self):
        return self.curr_position < 0

    def next(self):
        if self.islivedata():
            self.log("BEGIN next(): status={}".format(self.status))

        if self.islivedata() and self.status != "LIVE":
            self.log("%s - %.8f" % (self.status, self.data0.close[0]))
            return

        self.calculate_signals()

        self.execute_signals()

        self.strategyprocessor.on_next_trade_managers()

        self.printdebuginfo()

    def get_data_symbol(self, data):
        if self.islivedata():
            return data.symbol
        else:
            data_symbol_regex = "marketdata\/.*\/(.*)\/.*\/.*"
            data_symbol = re.search(data_symbol_regex, data.p.dataname)
            return data_symbol.group(1)

    def notify_order(self, order):
        if self.strategyprocessor.handle_order_completed_trade_managers(order):
            self.curr_position = 0
            self.position_avg_price = 0
            self.strategyprocessor.notify_analyzers()
            return

        self.log('notify_order() - order.ref={}, status={}, order.size={}, order.price={}, broker.cash={}, self.position.size = {}'.format(order.ref, order.Status[order.status], order.size, order.price, self.broker.getcash(), self.position.size))
        if order.status in [bt.Order.Created, bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = 'BUY COMPLETE, symbol={}, order.ref={}, {} - at {}'.format(self.get_data_symbol(self.data), order.ref, order.executed.price, bt.num2date(order.executed.dt))
                self.log(buytxt, True)
            else:
                selltxt = 'SELL COMPLETE, symbol={}, order.ref={}, {} - at {}'.format(self.get_data_symbol(self.data), order.ref, order.executed.price, bt.num2date(order.executed.dt))
                self.log(selltxt, True)
        elif order.status == order.Canceled:
            self.log('Order has been Cancelled: Symbol {}, Status {}, order.ref={}'.format(self.get_data_symbol(self.data), order.getstatusname(), order.ref), True)
        elif order.status in [order.Expired, order.Rejected]:
            self.log('Order has been Expired/Rejected: Symbol {}, Status {}, order.ref={}'.format(self.get_data_symbol(self.data), order.getstatusname(), order.ref), True)
            self.curr_position = 0
        elif order.status == order.Margin:
            self.log('notify_order() - ********** MARGIN CALL!! SKIP ORDER AND PREPARING FOR NEXT ORDERS!! **********', True)
            self.is_margin_condition = True
            if self.position.size == 0:  # If margin call ocurred during opening a new position, just skip opened position and wait for next signals
                self.curr_position = 0
            else:  # If margin call occurred during closing a position, then set curr_position to the same value as it was in previous cycle to give a chance to recover
                self.curr_position = -1 if self.position.size < 0 else 1 if self.position.size > 0 else 0

    def get_trade_log_profit_color(self, trade):
        return 'red' if trade.pnl < 0 else 'green'

    def notify_trade(self, trade):
        self.log('!!! BEGIN notify_trade() - id(self)={}, self.curr_position={}, trade.ref={}, self.broker.getcash()={}'.format(id(self), self.curr_position, trade.ref, round(self.broker.getcash(), 8)))

        if trade.justopened:
            self.tradesopen[trade.ref] = trade
            self.log('TRADE JUST OPENED: trade.size={}, trade.ref={}, trade.value={}, trade.commission={}'.format(trade.size, trade.ref, round(trade.value, 8), round(trade.commission, 8)))

        if trade.isclosed:
            self.tradesclosed[trade.ref] = trade
            self.log('---------------------------- TRADE CLOSED --------------------------')
            self.log("1: Data Name:                            {}".format(trade.data._name))
            self.log("2: Bar Num:                              {}".format(len(trade.data)))
            self.log("3: Current date:                         {}".format(self.data.datetime.date()))
            self.log('4: Status:                               Trade Complete')
            self.log('5: Ref:                                  {}'.format(trade.ref))
            self.log('6: PnL GROSS:                            {}'.format(round(trade.pnl, 8)))
            self.log('7: PnL NET:                              {}'.format(round(trade.pnlcomm, 8)))
            self.log(colored('OPERATION PROFIT, GROSS {:.8f}, NET {:.8f}'.format(trade.pnl, trade.pnlcomm), self.get_trade_log_profit_color(trade)))
            self.log('--------------------------------------------------------------------')
