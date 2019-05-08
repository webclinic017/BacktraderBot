#!/usr/bin/env python3

import backtrader as bt
from datetime import datetime

from bot.config import ENV, PRODUCTION
from bot.base import StrategyBase

class BasicRSI(StrategyBase):
    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using StochRSI strategy")

        self.sma_fast = bt.indicators.MovingAverageSimple(self.data0.close, period=20)
        self.sma_slow = bt.indicators.MovingAverageSimple(self.data0.close, period=200)
        self.rsi = bt.indicators.RelativeStrengthIndex()

        self.profit = 0

    def next(self):
        self.log("BEGIN next(): status={}".format(self.status))

        if self.status != "LIVE" and ENV == PRODUCTION:
            self.log("%s - $%.8f" % (self.status, self.data0.close[0]))
            return

        if self.order:
            if self.handle_pending_order(self.order) is False:
                return

        self.log("Inside next(): status={}".format(self.status))

        self.log("rsi={}".format(self.rsi[0]))
        if self.last_operation != "BUY":
            self.log("LONG CONDITION. rsi={}".format(self.rsi[0]))
            self.long()

        if self.last_operation != "SELL":
            self.log("SHORT CONDITION. rsi={}".format(self.rsi[0]))
            self.short()

    def TODOTTTT(self):
        # Manually close a position using the private method
        # 1 Get open positions with private_post_positions()
        # 2 Parse the position ID
        # 3 Cancel the position
        # 4 Update position pos.update(o_order.size, o_order.price)
        type = 'Post'
        endpoint = '/positions'
        params = {}
        positions = self.broker.private_end_point(type=type, endpoint=endpoint, params=params)
        for position in positions:
            id = position['id']
            type = 'Post'
            endpoint = '/position/close'
            params = {'position_id': id}
            result = self.broker.private_end_point(type=type, endpoint=endpoint, params=params)
            _pos = self.broker.getposition(d, clone=False)
            # A Price of NONE is returned form the close position endpoint!
            _pos.update(-self.position.size, None)

