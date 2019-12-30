import backtrader.indicators as btind
from strategies.genericstrategy import GenericStrategy


class S009_RSIMinMaxStrategy(GenericStrategy):
    '''
    This is an implementation of a strategy from TradingView - S009 RSI Min/Max v0.1 Strategy.
    '''
    params = (
        ("debug", False),
        ("startcash", 100000),
        ("needlong", True),
        ("needshort", True),
        ("rsiperiod", 14),
        ("rsilongopenvalue", 28),
        ("rsilongclosevalue", 69),
        ("rsishortopenvalue", 72),
        ("rsishortclosevalue", 31),
        ("sl", None),
        ("tslflag", None),
        ("tp", None),
        ("ttpdist", None),
        ("tbdist", None),
        ("numdca", None),
        ("dcainterval", None),
        ("fromyear", 2018),
        ("toyear", 2018),
        ("frommonth", 1),
        ("tomonth", 12),
        ("fromday", 1),
        ("today", 31),
    )

    def __init__(self):
        super().__init__()

        self.rsiVal = btind.RSI(self.data.close, period=self.p.rsiperiod, safediv=True)
        self.preOpenLongFlag   = [False] * 2
        self.preOpenShortFlag  = [False] * 2
        self.preCloseLongFlag  = [False] * 2
        self.preCloseShortFlag = [False] * 2

        self.openLongPositionCriteria = False
        self.openShortPositionCriteria = False
        self.signalOpenPosition = None
        self.closeLongPositionCriteria = False
        self.closeShortPositionCriteria = False
        self.signalClosePosition = None

    def isPreOpenLong(self):
        return self.preOpenLongFlag[-1] is True

    def isPreOpenShort(self):
        return self.preOpenShortFlag[-1] is True

    def isPreCloseLong(self):
        return self.preCloseLongFlag[-1] is True

    def isPreCloseShort(self):
        return self.preCloseShortFlag[-1] is True

    def isPositionClosed(self):
        return self.position.size == 0

    def isLongPositionOpen(self):
        return self.position.size > 0

    def isShortPositionOpen(self):
        return self.position.size < 0

    def isRsiEnteredBelowLevel(self, level):
        return self.rsiVal[-1] > level and self.rsiVal[0] <= level

    def isRsiEnteredAboveLevel(self, level):
        return self.rsiVal[-1] < level and self.rsiVal[0] >= level

    def hasReachedLongPositionTarget(self):
        return self.isPreCloseLong() and self.isRsiEnteredBelowLevel(self.p.rsilongclosevalue)

    def hasReachedShortPositionTarget(self):
        return self.isPreCloseShort() and self.isRsiEnteredAboveLevel(self.p.rsishortclosevalue)

    def calculate_signals(self):
        # Determine if pre-open criteria is met and set the flag
        if self.isPositionClosed() and not self.isPreOpenLong() and self.isRsiEnteredBelowLevel(self.p.rsilongopenvalue):
            self.preOpenLongFlag.append(True)
        else:
            self.preOpenLongFlag.append(self.preOpenLongFlag[-1])
        if self.isPositionClosed() and not self.isPreOpenShort() and self.isRsiEnteredAboveLevel(self.p.rsishortopenvalue):
            self.preOpenShortFlag.append(True)
        else:
            self.preOpenShortFlag.append(self.preOpenShortFlag[-1])

        # Determine if pre-close criteria is met and set the flag
        if self.isLongPositionOpen() and not self.isPreCloseLong() and self.isRsiEnteredAboveLevel(self.p.rsilongclosevalue):
            self.preCloseLongFlag.append(True)
        else:
            self.preCloseLongFlag.append(self.preCloseLongFlag[-1])
        if self.isShortPositionOpen() and not self.isPreCloseShort() and self.isRsiEnteredBelowLevel(self.p.rsishortclosevalue):
            self.preCloseShortFlag.append(True)
        else:
            self.preCloseShortFlag.append(self.preCloseShortFlag[-1])

        # Calculate signal to determine whether eligible to open a new position
        self.openLongPositionCriteria  = self.isPositionClosed() and self.isPreOpenLong()  and self.isRsiEnteredAboveLevel(self.p.rsilongopenvalue)
        self.openShortPositionCriteria = self.isPositionClosed() and self.isPreOpenShort() and self.isRsiEnteredBelowLevel(self.p.rsishortopenvalue)
        if self.openLongPositionCriteria is True:
            self.signalOpenPosition = 1
        else:
            if self.openShortPositionCriteria is True:
                self.signalOpenPosition = -1
            else:
                self.signalOpenPosition = None

        # Calculate signal to determine whether eligible to close existing position
        self.closeLongPositionCriteria = self.isLongPositionOpen() and self.hasReachedLongPositionTarget()
        self.closeShortPositionCriteria = self.isShortPositionOpen() and self.hasReachedShortPositionTarget()
        if self.closeLongPositionCriteria is True:
            self.signalClosePosition = 1
        else:
            if self.closeShortPositionCriteria is True:
                self.signalClosePosition = -1
            else:
                self.signalClosePosition = None

        if self.signalClosePosition == 1 or self.signalClosePosition == -1:
            self.preOpenLongFlag.append(False)
            self.preOpenShortFlag.append(False)
            self.preCloseLongFlag.append(False)
            self.preCloseShortFlag.append(False)

        # Signals
        self.is_open_long = True if self.signalOpenPosition == 1 else False
        self.is_close_long = True if self.signalClosePosition == 1 else False
        self.is_open_short = True if self.signalOpenPosition == -1 else False
        self.is_close_short = True if self.signalClosePosition == -1 else False

    def print_strategy_debug_info(self):
        self.log('self.rsiVal = {}'.format(self.rsiVal[0]))
        self.log('self.preOpenLongFlag = {}'.format(self.preOpenLongFlag[-1]))
        self.log('self.preOpenShortFlag = {}'.format(self.preOpenShortFlag[-1]))
        self.log('self.preCloseLongFlag = {}'.format(self.preCloseLongFlag[-1]))
        self.log('self.preCloseShortFlag = {}'.format(self.preCloseShortFlag[-1]))
        self.log('self.openLongPositionCriteria = {}'.format(self.openLongPositionCriteria))
        self.log('self.openShortPositionCriteria = {}'.format(self.openShortPositionCriteria))
        self.log('self.signalOpenPosition = {}'.format(self.signalOpenPosition))
        self.log('self.closeLongPositionCriteria = {}'.format(self.closeLongPositionCriteria))
        self.log('self.closeShortPositionCriteria = {}'.format(self.closeShortPositionCriteria))
        self.log('self.signalClosePosition = {}'.format(self.signalClosePosition))
