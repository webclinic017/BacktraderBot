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

class VariablePercentSizer(bt.Sizer):
    '''This sizer return percents of available cash

    Params:
      - ``percents`` (default: ``10``)
      - ``debug`` (default: ``False``)
    '''

    params = (
        ('percents', 10),
        ('debug', False),
    )

    def __init__(self):
        if self.p.debug:
            print('VariablePercentSizer.__init__(): self.params.percents={}'.format(self.params.percents))
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        value = self.broker.get_value()
        position = self.broker.getposition(data)
        comm = comminfo.p.commission
        com_adj_price = data.close[0] * (1 + (comm * 0)) # TODO: *2 for round trip
        size = round(value / com_adj_price * (self.params.percents / 100), 6) # Rounding to 6 digits as in TradingView backtesting window
        
        if self.p.debug:
            print('VariablePercentSizer._getsizing(): comm={}, value={}, data.close[0]={}, com_adj_price={}, size={}'.format(comm, value, data.close[0], com_adj_price, size))
        
        return size