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
      - ``cash`` (default: ``10000``)
      - ``debug`` (default: ``False``)
    '''

    params = (
        ('cash', 10000),
        ('debug', False),
    )

    def __init__(self):
        if self.p.debug:
            print('FixedCashSizer.__init__(): self.params.cash={}'.format(self.params.cash))
        pass

    def get_capital_value(self):
        if self.broker.get_value() < self.params.cash:
            return self.broker.get_value()
        else:
            return self.params.cash

    def _getsizing(self, comminfo, cash, data, isbuy):
        value = self.get_capital_value()
        price = data.close[0]
        size = value / (1.0 * price)

        if self.p.debug:
            print(
                'FixedCashSizer._getsizing(): self.broker.get_value()={}, data.close[0]={}, price={}, size={}'.format(
                    value, data.close[0], price, size))
        return size
