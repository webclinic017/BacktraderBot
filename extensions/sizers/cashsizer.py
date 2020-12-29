#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2019 Alex
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt


class FixedCashSizer(bt.Sizer):
    '''This sizer returns a number of contracts that can be acquired for fixed cash amount (e.g. USD, BTC..)
    Params:
      - ``lotsize`` (default: ``10000``)
      - ``debug``   (default: ``False``)
    '''

    ADJUSTMENT_FACTOR = 0.95

    params = (
        ('lotsize', 10000),
        ('commission', 0),
        ('risk', 0),
        ('debug', False),
    )

    def __init__(self):
        if self.p.debug:
            print('FixedCashSizer.__init__(): self.p.lotsize={}, self.p.commission={}, self.p.risk={}'.format(self.p.lotsize, self.p.commission, self.p.risk))
        pass

    def is_pre_margin_call_condition(self, cashamount):
        return self.broker.get_value() <= cashamount * (1 + 2 * self.p.commission)

    def get_capital(self, cashamount):
        if self.is_pre_margin_call_condition(cashamount):
            return round(self.broker.get_value() * self.ADJUSTMENT_FACTOR, 8)
        else:
            return self.ADJUSTMENT_FACTOR * cashamount

    def get_size(self, capital, price, risk_pct, sl_pct):
        if risk_pct and sl_pct and risk_pct <= sl_pct:
            return round(risk_pct / 100 * (capital / (sl_pct * price / 100)), 8)
        else:
            return round(capital / (1.0 * price), 8)

    def _getsizing(self, comminfo, cash, data, isbuy):
        capital = self.get_capital(self.p.lotsize)
        price = data.open[1]
        risk_pct = self.p.risk * 100
        sl_pct = self.strategy.get_current_sl_pct()
        size = self.get_size(capital, price, risk_pct, sl_pct)

        if self.p.debug:
            print('FixedCashSizer._getsizing(): capital()={}, data.close[0]={}, data.open[1]={}, price={}, risk={}, sl_pct={}, size={}'.format(capital, data.close[0], data.open[1], price, self.p.risk, sl_pct, size))
        return size
