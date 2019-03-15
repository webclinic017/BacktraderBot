import backtrader.indicators as btind
from datetime import datetime
import itertools
import pytz
from strategies.abstractstrategy import AbstractStrategy


class S009_RSIMinMaxStrategy(AbstractStrategy):
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
        self.is_up = False
        self.is_dn = False
        self.exit = False

        # To alternate amongst different tradeids
        self.tradeid = itertools.cycle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

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

    def next(self):
        # print("next(): id(self)={}".format(id(self)))
        # print("next() - Quick!")

        self.fromdt = datetime(self.p.fromyear, self.p.frommonth, self.p.fromday, 0, 0, 0)
        self.todt = datetime(self.p.toyear, self.p.tomonth, self.p.today, 23, 59, 59)
        self.currdt = self.data.datetime.datetime()

        self.gmt3_tz = pytz.timezone('Etc/GMT-3')
        self.fromdt = pytz.utc.localize(self.fromdt)
        self.todt = pytz.utc.localize(self.todt)
        self.currdt = self.gmt3_tz.localize(self.currdt, is_dst=True)
        if self.currdt > self.fromdt and self.currdt < self.todt:
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
            self.is_up = True if self.signalOpenPosition == 1 else False
            self.is_dn = True if self.signalOpenPosition == -1 else False
            self.exit = True if self.signalClosePosition == -1 or self.signalClosePosition == 1 else False

            # Trading
            self.printdebuginfonextinner()

            if self.curr_position < 0 and (self.is_up is True or self.exit is True):
                self.log('!!! BEFORE CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.is_up is True and self.p.needlong is True:
                self.log('!!! BEFORE OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.buy(tradeid=self.curtradeid)
                self.curr_position = 1
                self.log('!!! AFTER OPEN LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position > 0 and (self.is_dn is True or self.exit is True):
                self.log('!!! BEFORE CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.close(tradeid=self.curtradeid)
                self.curr_position = 0
                ddanalyzer = self.analyzers.dd
                ddanalyzer.notify_fund(self.broker.get_cash(), self.broker.get_value(), 0, 0)  # Notify DrawDown analyzer separately
                self.log('!!! AFTER CLOSE LONG !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

            if self.curr_position == 0 and self.is_dn is True and self.p.needshort is True:
                self.log('!!! BEFORE OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))
                self.curtradeid = next(self.tradeid)
                self.sell(tradeid=self.curtradeid)
                self.curr_position = -1
                self.log('!!! AFTER OPEN SHORT !!!, self.curr_position={}, cash={}'.format(self.curr_position, self.broker.getcash()))

        if self.currdt > self.todt:
            self.log('!!! Time passed beyond date range')
            if self.curr_position != 0:  # if 'curtradeid' in self:
                self.log('!!! Closing trade prematurely')
                self.close(tradeid=self.curtradeid)
            self.curr_position = 0

    def printdebuginfonextinner(self):
        self.log('---------------------- INSIDE NEXT DEBUG --------------------------')
        ddanalyzer = self.analyzers.dd.get_analysis()
        self.log('Drawdown: {}'.format(round(ddanalyzer.moneydown, 8)))
        self.log('Drawdown, %: {}%'.format(round(ddanalyzer.drawdown, 8)))
        self.log('self.curr_position = {}'.format(self.curr_position))
        self.log('self.position.size = {}'.format(self.position.size))
        self.log('self.position_avg_price = {}'.format(self.position_avg_price))
        self.log('self.broker.get_cash() = {}'.format(self.broker.get_cash()))
        self.log('self.broker.get_value() = {}'.format(self.broker.get_value()))
        self.log('self.data.open = {}'.format(self.data.open[0]))
        self.log('self.data.high = {}'.format(self.data.high[0]))
        self.log('self.data.low = {}'.format(self.data.low[0]))
        self.log('self.data.close = {}'.format(self.data.close[0]))
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
        self.log('self.is_up = {}'.format(self.is_up))
        self.log('self.is_dn = {}'.format(self.is_dn))
        self.log('self.exit = {}'.format(self.exit))
        self.log('----------------------')
