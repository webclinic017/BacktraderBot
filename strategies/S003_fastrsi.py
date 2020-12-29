import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S003_AlexNoroRobotBitMEXFastRSIStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S003 Alex (Noro) Robot BitMEX Fast RSI v1.0 strategy.
    '''

    params = (
        ("debug", False),
        ("wfo_cycle_id", None),
        ("wfo_cycle_training_id", None),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("rsiperiod", 7),
        ("rsibars", 3),
        ("rsilong", 30),
        ("rsishort", 70),
        ("useocf", True),
        ("useccf", True),
        ("openbars", 3),
        ("closebars", 1),
        ("useobf", True),
        ("usecbf", True),
        ("openbody", 20),
        ("closebody", 20),
        ("exitmode", None),
        ("sl", None),
        ("tslflag", None),
        ("tp", None),
        ("ttpdist", None),
        ("tbdist", None),
        ("numdca", None),
        ("dcainterval", None),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 12),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.curtradeid = -1
        self.curr_position = 0

        self.tradesopen = {}
        self.tradesclosed = {}

        # RSI
        self.rsi = btind.RSI(self.data.close, period=self.p.rsiperiod, safediv=True)
        self.rsidn = [0] * 2
        self.rsiup = [0] * 2
        self.rsidnok = [0] * 2
        self.rsiupok = [0] * 2

        # Body Filter
        self.body = abs(self.data.close - self.data.open)
        self.abody = btind.SimpleMovingAverage(self.body, period=10)
        self.openbodyok = [0, 0]
        self.closebodyok = [0, 0]

        # Color Filter
        self.bar = [0] * 2
        self.gbar = [0] * 2
        self.rbar = [0] * 2

        self.check_gbar_openbars = [0] * 2
        self.check_rbar_openbars = [0] * 2
        self.check_gbar_closebars = [0] * 2
        self.check_rbar_closebars = [0] * 2 

        self.opengbarok = [0] * 2
        self.openrbarok = [0] * 2
        self.closegbarok = [0] * 2
        self.closerbarok = [0] * 2

    def calculate_signals(self):
        # RSI
        if self.rsi[0] < self.p.rsilong:
            self.rsidn.append(1)
        else:
            self.rsidn.append(0)
        if self.rsi[0] > self.p.rsishort:
            self.rsiup.append(1)
        else:
            self.rsiup.append(0)

        if self.check_arr_equal(self.rsidn, 1, self.p.rsibars):
            self.rsidnok.append(1)
        else:
            self.rsidnok.append(0)
        if self.check_arr_equal(self.rsiup, 1, self.p.rsibars):
            self.rsiupok.append(1)
        else:
            self.rsiupok.append(0)

        # Body Filter
        if self.body[0] >= self.abody[0] / 100 * self.p.openbody or self.p.useobf is False:
            self.openbodyok.append(1)
        else:
            self.openbodyok.append(0)
        if self.body[0] >= self.abody[0] / 100 * self.p.closebody or self.p.usecbf is False:
            self.closebodyok.append(1)
        else:
            self.closebodyok.append(0)

        # Color Filter
        if self.data.close[0] > self.data.open[0]:
            self.bar.append(1)
        else:
            if self.data.close[0] < self.data.open[0]:
                self.bar.append(-1)
            else:
                self.bar.append(0)

        if self.bar[-1] == 1:
            self.gbar.append(1)
        else:
            self.gbar.append(0)
        if self.bar[-1] == -1:
            self.rbar.append(1)
        else:
            self.rbar.append(0)

        self.check_gbar_openbars.append(self.check_arr_equal(self.gbar, 1, self.p.openbars))
        self.check_rbar_openbars.append(self.check_arr_equal(self.rbar, 1, self.p.openbars))
        self.check_gbar_closebars.append(self.check_arr_equal(self.gbar, 1, self.p.closebars)) 
        self.check_rbar_closebars.append(self.check_arr_equal(self.rbar, 1, self.p.closebars))

        if self.check_gbar_openbars[-1] is True or self.p.useocf is False:
            self.opengbarok.append(1)
        else:
            self.opengbarok.append(0)
        if self.check_rbar_openbars[-1] is True or self.p.useocf is False:
            self.openrbarok.append(1)
        else:
            self.openrbarok.append(0)
        if self.check_gbar_closebars[-1] is True or self.p.useccf is False:
            self.closegbarok.append(1)
        else:
            self.closegbarok.append(0)
        if self.check_rbar_closebars[-1] is True or self.p.useccf is False:
            self.closerbarok.append(1)
        else:
            self.closerbarok.append(0)

        # Signals
        self.is_open_long = True if self.position.size == 0 and self.openrbarok[-1] == 1 and self.rsidnok[-1] == 1 and self.openbodyok[-1] == 1 else False
        self.is_close_long = True if (self.position.size > 0 and self.closegbarok[-1] == 1 and self.rsi[0] > self.p.rsilong) and self.closebodyok[-1] == 1 else False
        self.is_open_short = True if self.position.size == 0 and self.opengbarok[-1] == 1 and self.rsiupok[-1] == 1 and self.openbodyok[-1] == 1 else False
        self.is_close_short = True if (self.position.size < 0 and self.closerbarok[-1] == 1 and self.rsi[0] < self.p.rsishort) and self.closebodyok[-1] == 1 else False

    def print_strategy_debug_info(self):
        self.log('self.rsi = {}'.format(self.rsi[0]))
        self.log('self.rsidn = {}'.format(self.rsidn[-1]))
        self.log('self.rsiup = {}'.format(self.rsiup[-1]))
        self.log('self.rsidnok = {}'.format(self.rsidnok[-1]))
        self.log('self.rsiupok = {}'.format(self.rsiupok[-1]))
        self.log('self.body = {}'.format(self.body[0]))
        self.log('self.abody = {}'.format(self.abody[0]))
        self.log('self.openbodyok = {}'.format(self.openbodyok[-1]))
        self.log('self.closebodyok = {}'.format(self.closebodyok[-1]))
        self.log('self.bar = {}'.format(self.bar[-1]))
        self.log('self.gbar = {}'.format(self.gbar[-1]))
        self.log('self.rbar = {}'.format(self.rbar[-1]))
        self.log('self.check_gbar_openbars = {}'.format(self.check_gbar_openbars[-1]))
        self.log('self.check_rbar_openbars = {}'.format(self.check_rbar_openbars[-1]))
        self.log('self.check_gbar_closebars = {}'.format(self.check_gbar_closebars[-1]))
        self.log('self.check_rbar_closebars = {}'.format(self.check_rbar_closebars[-1]))
        self.log('self.opengbarok = {}'.format(self.opengbarok[-1]))
        self.log('self.openrbarok = {}'.format(self.openrbarok[-1]))
        self.log('self.closegbarok = {}'.format(self.closegbarok[-1]))
        self.log('self.closerbarok = {}'.format(self.closerbarok[-1]))

