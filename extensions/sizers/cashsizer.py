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
      - ``cashamount`` (default: ``10000``)
      - ``debug`` (default: ``False``)
    '''

    _PREMARGINCALL_ADJUSTMENT_RATIO = 0.9

    params = (
        ('cashamount', 10000),
        ('commission', 0.002),
        ('debug', False),
    )

    def __init__(self):
        if self.p.debug:
            print('FixedCashSizer.__init__(): self.params.cashamount={}'.format(self.p.cashamount))
        pass

    def is_pre_margin_call_condition(self):
        return self.broker.get_value() <= self.p.cashamount * (1 + 2 * self.p.commission)

    def get_capital_value(self):
        if self.is_pre_margin_call_condition():
            return round(self.broker.get_value() * self._PREMARGINCALL_ADJUSTMENT_RATIO)
        else:
            return self.p.cashamount

    def _getsizing(self, comminfo, cash, data, isbuy):
        value = self.get_capital_value()
        price = data.open[1]
        size = round(value / (1.0 * price), 6)

        if self.p.debug:
            print(
                'FixedCashSizer._getsizing(): self.get_capital_value()={}, data.close[0]={}, data.open[1]={}, price={}, size={}'.format(
                    value, data.close[0], data.open[1], price, size))
        return size
