#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2018 Alex
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict
from backtrader.utils.py3 import MAXINT

__all__ = ['TVTradeAnalyzer']

class TVTradeAnalyzer(Analyzer):
    '''
    Modified version of Backtrader's TradeAnalyzer that calculates NetProfit, GrossProfit, GrossLoss, ProfitFactor, BuyAndHoldReturn values in the same way as in tTradingView
    '''
    params = (
        ('cash', 0),
    )

    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self.rets.total.total = 0
        self.buyandholdcalcbegin = False
        self.buyandholdnumshares = 0
        self.buyandholdstartvalue = 0

    def stop(self):
        super(TVTradeAnalyzer, self).stop()
        self.rets._close()

    def next(self):
        trades = self.rets
        if self.buyandholdcalcbegin == True:
            trades.total.buyandholdreturn = self.data.close[0] * self.buyandholdnumshares - self.buyandholdstartvalue
            trades.total.buyandholdreturnpct = 100 * trades.total.buyandholdreturn / self.buyandholdstartvalue

    def notify_trade(self, trade):
        if trade.justopened:
            # Trade just opened
            self.rets.total.total += 1
            self.rets.total.open += 1
            if self.buyandholdcalcbegin == False:
                self.buyandholdcalcbegin = True
                self.buyandholdnumshares = int(self.p.cash / trade.price)
                self.buyandholdstartvalue = self.buyandholdnumshares * trade.price         

        elif trade.status == trade.Closed:
            trades = self.rets

            res = AutoDict()
            # Trade just closed

            won = res.won = int(trade.pnlcomm >= 0.0)
            lost = res.lost = int(not won)
            tlong = res.tlong = trade.long
            tshort = res.tshort = not trade.long

            trades.total.open -= 1
            trades.total.closed += 1

            # Streak
            for wlname in ['won', 'lost']:
                wl = res[wlname]

                trades.streak[wlname].current *= wl
                trades.streak[wlname].current += wl

                ls = trades.streak[wlname].longest or 0
                trades.streak[wlname].longest = \
                    max(ls, trades.streak[wlname].current)

            trpnl = trades.pnl
            trpnl.gross.total += trade.pnl
            trpnl.gross.average = trades.pnl.gross.total / trades.total.closed
            trpnl.net.total += trade.pnlcomm
            trpnl.net.average = trades.pnl.net.total / trades.total.closed

            # Won/Lost statistics
            for wlname in ['won', 'lost']:
                wl = res[wlname]
                trwl = trades[wlname]

                trwl.total += wl  # won.total / lost.total

                trwlpnl = trwl.pnl
                pnlcomm = trade.pnlcomm * wl

                trwlpnl.total += pnlcomm
                trwlpnl.average = trwlpnl.total / (trwl.total or 1.0)

                wm = trwlpnl.max or 0.0
                func = max if wlname == 'won' else min
                trwlpnl.max = func(wm, pnlcomm)

            trades.pnl.grossprofit.total += (trade.pnlcomm if trade.pnlcomm >= 0 else 0)
            trades.pnl.grossprofit.average = (trades.pnl.grossprofit.total / trades.won.total) if trades.won.total > 0 else 0
            trades.pnl.grossloss.total += (trade.pnlcomm if trade.pnlcomm < 0 else 0)
            trades.pnl.grossloss.average = (trades.pnl.grossloss.total / trades.lost.total) if trades.lost.total > 0 else 0
            trades.pnl.netprofit.total = trades.pnl.grossprofit.total + trades.pnl.grossloss.total
            trades.total.profitfactor = abs(trades.pnl.grossprofit.total / trades.pnl.grossloss.total) if trades.pnl.grossloss.total != 0 else 0

            # Long/Short statistics
            for tname in ['long', 'short']:
                trls = trades[tname]
                ls = res['t' + tname]

                trls.total += ls  # long.total / short.total
                trls.pnl.total += trade.pnlcomm * ls
                trls.pnl.average = trls.pnl.total / (trls.total or 1.0)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]
                    pnlcomm = trade.pnlcomm * wl * ls

                    trls[wlname] += wl * ls  # long.won / short.won

                    trls.pnl[wlname].total += pnlcomm
                    trls.pnl[wlname].average = \
                        trls.pnl[wlname].total / (trls[wlname] or 1.0)

                    wm = trls.pnl[wlname].max or 0.0
                    func = max if wlname == 'won' else min
                    trls.pnl[wlname].max = func(wm, pnlcomm)

            # Length
            trades.len.total += trade.barlen
            trades.len.average = trades.len.total / trades.total.closed
            ml = trades.len.max or 0
            trades.len.max = max(ml, trade.barlen)

            ml = trades.len.min or MAXINT
            trades.len.min = min(ml, trade.barlen)

            # Length Won/Lost
            for wlname in ['won', 'lost']:
                trwl = trades.len[wlname]
                wl = res[wlname]

                trwl.total += trade.barlen * wl
                trwl.average = trwl.total / (trades[wlname].total or 1.0)

                m = trwl.max or 0
                trwl.max = max(m, trade.barlen * wl)
                if trade.barlen * wl:
                    m = trwl.min or MAXINT
                    trwl.min = min(m, trade.barlen * wl)

            # Length Long/Short
            for lsname in ['long', 'short']:
                trls = trades.len[lsname]  # trades.len.long
                ls = res['t' + lsname]  # tlong/tshort

                barlen = trade.barlen * ls

                trls.total += barlen  # trades.len.long.total
                total_ls = trades[lsname].total   # trades.long.total
                trls.average = trls.total / (total_ls or 1.0)

                # max/min
                m = trls.max or 0
                trls.max = max(m, barlen)
                m = trls.min or MAXINT
                trls.min = min(m, barlen or m)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]  # won/lost

                    barlen2 = trade.barlen * ls * wl

                    trls_wl = trls[wlname]  # trades.len.long.won
                    trls_wl.total += barlen2  # trades.len.long.won.total

                    trls_wl.average = \
                        trls_wl.total / (trades[lsname][wlname] or 1.0)

                    # max/min
                    m = trls_wl.max or 0
                    trls_wl.max = max(m, barlen2)
                    m = trls_wl.min or MAXINT
                    trls_wl.min = min(m, barlen2 or m)
