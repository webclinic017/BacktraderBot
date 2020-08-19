import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy
from random import random
from random import seed

MAX_NUMBER_TRADES = 100


class Test01FlipCoinStrategy(GenericStrategy):
    params = (
        ("debug", False),
        ("startcash", 1500),
        ("needlong", True),
        ("needshort", True),
        ("exitmode", 1),
        ("sl", 0),
        ("tslflag", False),
        ("tp", 0),
        ("ttpdist", 0),
        ("tbdist", 0),
        ("numdca", 0),
        ("dcainterval", 0),
        ("fromyear", 2020),
        ("toyear", 2020),
        ("frommonth", 1),
        ("tomonth", 1),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

    def exists(self, obj, chain):
        _key = chain.pop(0)
        if _key in obj:
            return self.exists(obj[_key], chain) if chain else obj[_key]

    def check_max_number_trades(self):
        analyzer = self.analyzers.ta.get_analysis()
        total_closed = analyzer.total.closed if self.exists(analyzer, ['total', 'closed']) else 0
        if total_closed > MAX_NUMBER_TRADES:
            self.log('!!! Max number of trades reached for test: {}'.format(MAX_NUMBER_TRADES))

            if self.is_strategy_dca_mode_enabled():
                ta_analyzer = self.analyzers.ta
                ta_analyzer.skip_trade_update_flag = True
                ddanalyzer = self.analyzers.dd
                ddanalyzer.skip_trade_update_flag = True

            self.deactivate_entry_trade_managers()
            if self.curr_position != 0:
                self.log('!!! Closing the trade prematurely')
                self.signal_close_position(self.is_long_position())
            self.curr_position = 0
            self.position_avg_price = 0
            self.broker.cerebro.runstop()

    def calculate_signals(self):

        self.check_max_number_trades()

        rnd = random() - 0.5
        self.up = 1 if self.curr_position == 0 and rnd > 0 else 0
        self.dn = 1 if self.curr_position == 0 and rnd < 0 else 0

        self.is_open_long = True if self.up == 1 else False
        self.is_close_long = False
        self.is_open_short = True if self.dn == 1 else False
        self.is_close_short = False

    def print_strategy_debug_info(self):
        pass