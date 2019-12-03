import backtrader as bt
from abc import abstractmethod
import itertools
from datetime import datetime
import pytz
from strategies.managers.sltpmanager import SLTPManager
from strategies.managers.trailingbuymanager import TrailingBuyManager
from strategies.managers.dcamodemanager import DcaModeManager
from strategies.helper.ococontext import OcoContext
from bot.config.bot_strategy_config import BotStrategyConfig
from strategies.processors.livetradingstrategyprocessor import LiveTradingStrategyProcessor
from strategies.processors.backtestingstrategyprocessor import BacktestingStrategyProcessor
from termcolor import colored
import re

DEFAULT_CAPITAL_STOPLOSS_VALUE_PCT = -50


class ParametersValidator(object):
    @classmethod
    def validate_params(cls, params):
        if not params.get("needlong") and not params.get("needshort"):
            raise ValueError("Either 'needlong' or 'needshort' parameters must be provided")
        #if params.get("sl") and not params.get("tp") or not params.get("sl") and params.get("tp"):
        #    raise ValueError("Both the STOP-LOSS ('sl') and TAKE-PROFIT ('tp') parameters should be defined together")
        if params.get("tslflag") and not params.get("sl"):
            raise ValueError("The TRAILING STOP-LOSS ('tslflag') parameter should be provided with STOP-LOSS ('sl') parameter")
        if params.get("ttpdist") and not params.get("tp"):
            raise ValueError("The TRAILING TAKE-PROFIT ('ttpdist') parameter cannot be provided without TAKE-PROFIT ('tp') parameter")
        if params.get("sl") and params.get("tp") and params.get("tp") / (1.0 * params.get("sl")) < 0.5:
            raise ValueError("The TAKE-PROFIT ('tp') / STOP-LOSS ('sl') ratio should be more than 0.5")
        if params.get("dcainterval") and not params.get("numdca") or not params.get("dcainterval") and params.get("numdca"):
            raise ValueError("Both DCA-MODE parameters 'dcainterval' and 'numdca' must be provided")
        if params.get("numdca") and params.get("numdca") < 2:
            raise ValueError("The DCA-MODE parameters 'dcainterval' must greater or equal 2")
        if params.get("dcainterval") and params.get("numdca") and params.get("tbdist"):
            raise ValueError("Both TRAILING-BUY ('tbdist') and DCA-MODE ('dcainterval'/'numdca') parameters can not be specified: only one mode (TRAILING-BUY or DCA-MODE) can be used at the same time")
        if params.get("dcainterval") and params.get("numdca") and (params.get("tslflag") or params.get("ttpdist")):
            raise ValueError("The DCA-MODE ('dcainterval'/'numdca') parameters cannot be configured together with TRAILING STOP-LOSS ('tslflag') or TRAILING TAKE-PROFIT ('ttpdist') parameters. Only STOP-LOSS ('sl') and TAKE-PROFIT ('tp') parameters allowed")
        if params.get("dcainterval") and params.get("numdca") and params.get("sl") and params.get("sl") <= params.get("dcainterval") * params.get("numdca"):
            raise ValueError("The DCA-MODE ('dcainterval'/'numdca') together with STOP-LOSS ('sl') parameters must be configured in such way that 'sl' should be greater than 'dcainterval'*'numdca'")
        if params.get("dcainterval") and params.get("numdca") and not params.get("tp"):
            raise ValueError("The DCA-MODE ('dcainterval'/'numdca') parameters must be configured together with TAKE-PROFIT ('tp') parameter")
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
        self.oco_context = OcoContext()
        self.sltpmanager = SLTPManager(self, self.oco_context)
        self.trailingbuymanager = TrailingBuyManager(self)
        self.dcamodemanager = DcaModeManager(self, self.strategyprocessor, self.oco_context)

        self.is_error_condition = False
        self.is_margin_condition = False

        self.skip_bar_on_tb_completed = False
        self.capital_stoploss_fired_flow_control_flag = False

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

    def is_order_accepted_in_broker(self, order):
        return order.status in [bt.Order.Accepted, bt.Order.Partial, bt.Order.Completed, bt.Order.Canceled, bt.Order.Expired, bt.Order.Margin, bt.Order.Rejected]

    def activate_trade_entry_managers(self, tradeid, last_price, is_long):
        self.trailingbuymanager.activate_tb(tradeid, last_price, is_long)
        self.dcamodemanager.activate_dca_mode(tradeid, last_price, is_long)

    def activate_trade_managers(self, tradeid, pos_price, pos_size, is_long):
        self.sltpmanager.activate_sl(tradeid, pos_price, pos_size, is_long)
        self.sltpmanager.activate_tp(tradeid, pos_price, pos_size, is_long)

    def on_next_trade_managers(self):
        self.sltpmanager.move_targets()
        self.trailingbuymanager.move_targets()

        self.sltpmanager.sl_on_next()
        self.sltpmanager.tp_on_next()
        self.trailingbuymanager.tb_on_next()

    def handle_order_completed_trailing_buy(self, order):
        return self.trailingbuymanager.handle_order_completed(order)

    def handle_order_completed_dca_mode(self, order):
        return self.dcamodemanager.handle_order_completed(order)

    def handle_order_completed_trade_managers(self, order):
        return self.sltpmanager.handle_order_completed(order)

    def deactivate_entry_trade_managers(self):
        self.dcamodemanager.dca_mode_deactivate()
        self.trailingbuymanager.tb_deactivate()

    def deactivate_trade_managers(self):
        self.sltpmanager.sl_deactivate()
        self.sltpmanager.tp_deactivate()

    def is_allow_signals_execution(self):
        return not self.sltpmanager.is_tp_mode_activated() and not self.trailingbuymanager.is_tb_mode_activated() and not self.dcamodemanager.is_dca_mode_activated()

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
        if self.trailingbuymanager.is_tb_enabled:
            self.tb_signal_open_position(is_long)
        elif self.dcamodemanager.is_dca_mode_enabled:
            self.dcamode_signal_open_position(is_long)
        else:
            self.generic_signal_open_position(is_long)

    def generic_signal_open_position(self, is_long):
        cash = self.broker.getcash()
        side_str = self.get_side_str(is_long)
        self.log('!!! BEFORE - SIGNAL OPEN POSITION {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))
        self.curtradeid = next(self.tradeid)
        if is_long:
            base_order = self.strategyprocessor.open_long_position()
            self.curr_position = 1
        else:
            base_order = self.strategyprocessor.open_short_position()
            self.curr_position = -1

        self.position_avg_price = self.data.close[0]
        self.activate_trade_managers(self.curtradeid, self.position_avg_price, base_order.size, is_long)
        self.log('!!! AFTER - SIGNAL OPEN POSITION {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))

    def tb_signal_open_position(self, is_long):
        cash = self.broker.getcash()
        side_str = self.get_side_str(is_long)
        last_price = self.data.close[0]

        self.log('!!! BEFORE - TRAILING-BUY MODE - START {} !!!'.format(side_str, self.curr_position, cash))
        self.curtradeid = next(self.tradeid)
        self.activate_trade_entry_managers(self.curtradeid, last_price, is_long)
        self.log('!!! AFTER - TRAILING-BUY MODE - START {} !!!'.format(side_str, self.curr_position, cash))

    def submit_base_order(self, is_long):
        order_size = self.dcamodemanager.get_desired_order_size(is_long)
        if is_long:
            base_order = self.strategyprocessor.open_long_position(order_size)
            self.curr_position = 1
        else:
            base_order = self.strategyprocessor.open_short_position(order_size)
            self.curr_position = -1

        self.log('Submitted a new BASE order for DCA-MODE: is_long={}, base_order.ref={}, base_order.size={}, base_order.price={}, base_order.side={}'.format(
            is_long, base_order.ref, base_order.size, base_order.price, base_order.ordtypename()))
        return base_order

    def dcamode_signal_open_position(self, is_long):
        cash = self.broker.getcash()
        side_str = self.get_side_str(is_long)
        last_price = self.data.close[0]

        self.log('!!! BEFORE - DCA MODE - START {} !!!'.format(side_str, self.curr_position, cash))
        self.curtradeid = next(self.tradeid)

        self.log('DCA MODE: Submitting BASE order for tradeid={}, last_price={}, is_long={}'.format(self.curtradeid, last_price, is_long))
        base_order = self.submit_base_order(is_long)

        self.position_avg_price = last_price
        self.activate_trade_managers(self.curtradeid, self.position_avg_price, base_order.size, is_long)
        self.activate_trade_entry_managers(self.curtradeid, last_price, is_long)

        self.log('!!! AFTER - DCA MODE - START {} !!!'.format(side_str, self.curr_position, cash))

    def signal_close_position(self, is_long):
        cash = self.broker.getcash()
        side_str = self.get_side_str(is_long)

        self.log('!!! BEFORE - SIGNAL CLOSE POSITION {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))
        self.strategyprocessor.close_position()
        self.curr_position = 0
        self.position_avg_price = 0
        self.strategyprocessor.notify_analyzers()
        self.deactivate_entry_trade_managers()
        self.deactivate_trade_managers()
        self.log('!!! AFTER - SIGNAL CLOSE POSITION {} !!!, self.curr_position={}, cash={}'.format(side_str, self.curr_position, cash))

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def set_processing_status(self):
        if self.islivedata():
            return

        ta_analyzer = self.analyzers.ta
        if self.is_error_condition:
            ta_analyzer.update_processing_status("Error")
        elif self.is_margin_condition:
            ta_analyzer.update_processing_status("Margin")
        else:
            analysis = ta_analyzer.get_analysis()
            total_open = analysis.total.open if self.exists(analysis, ['total', 'open']) else 0
            if total_open != 0:
                ta_analyzer.update_processing_status("Open Trades")
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

        if self.is_allow_signals_execution():
            if self.islivedata() or self.currdt > self.fromdt and self.currdt < self.todt:
                if self.is_short_position() and self.is_close_short:
                    self.signal_close_position(False)

                if self.is_position_closed() and self.p.needlong and self.is_open_long:
                    self.signal_open_position(True)

                if self.is_long_position() and self.is_close_long:
                    self.signal_close_position(True)

                if self.is_position_closed() and self.p.needshort and self.is_open_short:
                    self.signal_open_position(False)

        if not self.islivedata() and self.currdt > self.todt:
            self.log('!!! Time has passed beyond date range')
            self.deactivate_entry_trade_managers()
            if self.curr_position != 0:
                self.log('!!! Closing trade prematurely')
                self.signal_close_position(self.is_long_position())
            self.curr_position = 0
            self.position_avg_price = 0

    def print_strategy_debug_info(self):
        pass

    def is_position_closed(self):
        return self.curr_position == 0

    def is_long_position(self):
        return self.curr_position > 0

    def is_short_position(self):
        return self.curr_position < 0

    def handle_capital_stoploss(self):
        realized_pl = round((self.broker.getvalue() - self.p.startcash) * 100 / self.p.startcash, 2)
        if not self.capital_stoploss_fired_flow_control_flag and realized_pl <= DEFAULT_CAPITAL_STOPLOSS_VALUE_PCT:
            self.log("The Unrealized P/L of the strategy={}% has exceeded the Capital STOP-LOSS Value={}%. The strategy will be completed prematurely.".format(realized_pl, DEFAULT_CAPITAL_STOPLOSS_VALUE_PCT))
            self.generic_close(tradeid=self.curtradeid)
            self.curr_position = 0
            self.position_avg_price = 0
            self.strategyprocessor.notify_analyzers()
            self.deactivate_entry_trade_managers()
            self.deactivate_trade_managers()
            self.capital_stoploss_fired_flow_control_flag = True
            return True
        if self.capital_stoploss_fired_flow_control_flag and self.position.size == 0:
            self.broker.cerebro.runstop()
            return True
        return False

    def next(self):
        try:
            if self.skip_bar_on_tb_completed:
                self.log("next(): skip_bar_on_tb_completed={}. Skip next() processing.".format(self.skip_bar_on_tb_completed))
                self.skip_bar_on_tb_completed = False
                self.print_all_debug_info()
                return

            if self.islivedata():
                self.log("BEGIN next(): status={}".format(self.status))

            if self.islivedata() and self.status != "LIVE":
                self.log("%s - %.8f" % (self.status, self.data0.close[0]))
                return

            #if self.handle_capital_stoploss():
            #    return

            self.calculate_signals()

            self.execute_signals()

            self.on_next_trade_managers()

            self.print_all_debug_info()
        except Exception as e:
            self.is_error_condition = True
            self.broker.cerebro.runstop()
            raise e

    def get_data_symbol(self, data):
        if self.islivedata():
            return data.symbol
        else:
            data_symbol_regex = "marketdata\/.*\/(.*)\/.*\/.*"
            data_symbol = re.search(data_symbol_regex, data.p.dataname)
            return data_symbol.group(1)

    def notify_order(self, order):
        if self.handle_order_completed_trailing_buy(order):
            self.activate_trade_managers(self.curtradeid, self.position_avg_price, order.size, self.is_long_position())
            self.skip_bar_on_tb_completed = True
            return

        if self.handle_order_completed_dca_mode(order):
            return

        if self.handle_order_completed_trade_managers(order):
            self.deactivate_entry_trade_managers()
            self.curr_position = 0
            self.position_avg_price = 0
            self.strategyprocessor.notify_analyzers()
            return

        self.log('notify_order() - order.ref={}, status={}, order.size={}, order.price={}, broker.cash={}, self.position.size = {}'.format(order.ref, order.getstatusname(), order.size, order.price, self.broker.getcash(), self.position.size))
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
            self.broker.cerebro.runstop()

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

    def stop(self):
        self.set_processing_status()

    def print_all_debug_info(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        if not self.islivedata():
            ddanalyzer = self.analyzers.dd.get_analysis()
            self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
            self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
            self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
            self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.curtradeid = {}'.format(self.curtradeid))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.position.price = {}'.format(self.position.price))
        self.log('self.position_avg_price = {}'.format(self.position_avg_price))
        self.log('self.data.datetime[0] = {}'.format(self.data.datetime.datetime()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))

        self.print_strategy_debug_info()

        self.log('self.is_open_long = {}'.format(self.is_open_long))
        self.log('self.is_close_long = {}'.format(self.is_close_long))
        self.log('self.is_open_short = {}'.format(self.is_open_short))
        self.log('self.is_close_short = {}'.format(self.is_close_short))
        self.sltpmanager.log_state()
        self.trailingbuymanager.log_state()
        self.dcamodemanager.log_state()
        self.log('----------------------')
