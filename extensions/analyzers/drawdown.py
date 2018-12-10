#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2018 Alex
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader.utils import AutoOrderedDict

__all__ = ['TVNetProfitDrawDown']

class TVNetProfitDrawDown(bt.Analyzer):
    '''This analyzer calculates trading system drawdowns stats such as drawdown
    values in %s and in dollars, max drawdown in %s and in dollars, drawdown
    length and drawdown max length

    Methods:

      - ``get_analysis``

        Returns a dictionary (with . notation support and subdctionaries) with
        drawdown stats as values, the following keys/attributes are available:

        - ``drawdown`` - drawdown value in 0.xx %
        - ``moneydown`` - drawdown value in monetary units
        - ``len`` - drawdown length

        - ``max.drawdown`` - max drawdown value in 0.xx %
        - ``max.moneydown`` - max drawdown value in monetary units
        - ``max.len`` - max drawdown length
    '''

    def start(self):
        super(TVNetProfitDrawDown, self).start()
        self._fundmode = self.strategy.broker.fundmode

    def create_analysis(self):
        self.rets = AutoOrderedDict()  # dict with . notation

        self.rets.len = 0
        self.rets.drawdown = 0.0
        self.rets.moneydown = 0.0

        self.rets.max.len = 0.0
        self.rets.max.drawdown = 0.0
        self.rets.max.moneydown = 0.0

        self._currvalue = 0
        self._maxportfoliovalue = 0

    def stop(self):
        self.rets._close()  # . notation cannot create more keys

    def notify_fund(self, cash, value, fundvalue, shares):
        self._currvalue = value  # record current value
        #print('!! INSIDE notify_fund self._currvalue={}'.format(self._currvalue))

    def notify_trade(self,trade):
        #if trade.justopened:
            #print('!! INSIDE notify_trade JUSTOPENED self._currvalue={}'.format(self._currvalue))
            
        if trade.isclosed:
            r = self.rets
            tradeclosevalue = self._currvalue
            #print('!! INSIDE notify_trade CLOSED tradeclosevalue={}, self._maxportfoliovalue={}'.format(tradeclosevalue, self._maxportfoliovalue))
            if tradeclosevalue < self._maxportfoliovalue:
                r.moneydown = moneydown = tradeclosevalue - self._maxportfoliovalue
                r.drawdown = drawdown = 100.0 * moneydown / self._maxportfoliovalue
                r.len = r.len + 1 if drawdown else 0
            else:
                self._maxportfoliovalue = tradeclosevalue
                r.moneydown = moneydown = 0
                r.drawdown = drawdown = 0
                r.len = 0

            # maximum drawdown values
            r.max.moneydown = min(r.max.moneydown, moneydown)
            r.max.drawdown  = min(r.max.drawdown, drawdown)
            r.max.len = max(r.max.len, r.len)

            #print('!! INSIDE notify_trade CLOSED self._maxportfoliovalue={}'.format(self._maxportfoliovalue))
            #print('!! INSIDE notify_trade CLOSED r.moneydown={}'.format(r.moneydown))
            #print('!! INSIDE notify_trade CLOSED r.drawdown={}'.format(r.drawdown))
            #print('!! INSIDE notify_trade CLOSED r.len={}'.format(r.len))
            #print('!! INSIDE notify_trade CLOSED r.max.moneydown={}'.format(r.max.moneydown))
            #print('!! INSIDE notify_trade CLOSED r.max.drawdown={}'.format(r.max.drawdown))
            #print('!! INSIDE notify_trade CLOSED r.max.len={}'.format(r.max.len))
            #print('!! END INSIDE notify_trade CLOSED')


