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
from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict
from backtrader.utils.py3 import MAXINT
from calendar import monthrange
import json

__all__ = ['TVTradeAnalyzer']

class TVTradeAnalyzer(Analyzer):
    '''
    Modified version of Backtrader's TradeAnalyzer that calculates NetProfit, GrossProfit, GrossLoss, ProfitFactor, BuyAndHoldReturn values in the same way as in TradingView
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
        self.netprofits_data = AutoOrderedDict()

    def set_netprofit_value(self, value):
        self.netprofits_data[self.get_currentdate()] = value

    def get_netprofits_data(self):
        result = {}
        counter = 0
        for date, netprofit in self.netprofits_data.items():
            counter += 1
            result[counter] = round(netprofit, 2)
        return json.dumps(result)

    def get_currentdate(self):
        return bt.num2date(self.data.datetime[0])

    def getdaterange(self, fromyear, frommonth, fromday, toyear, tomonth, today):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(fromyear, frommonth, fromday, toyear, tomonth, today)

    def get_month_daterange(self, date):
        return self.getdaterange(date.year, date.month, 1, date.year, date.month, self.get_month_num_days(date.year, date.month))

    def get_currentmonth_daterange(self):
        curr_datetime = self.get_currentdate()
        return self.get_month_daterange(curr_datetime)

    def get_month_num_days(self, year, month):
        return monthrange(year, month)[1]

    def get_monthly_stats_entry(self, curr_month_daterange_str):
        trades = self.rets

        entry = trades.monthly_stats[curr_month_daterange_str]
        if len(entry) == 0:
            entry = trades.monthly_stats[curr_month_daterange_str] = AutoOrderedDict()
        return entry

    def check_next_month(self, prev_datetime, curr_datetime):
        months_diff = (curr_datetime.year - prev_datetime.year) * 12 + (curr_datetime.month - prev_datetime.month)
        return months_diff >= 1

    def update_tradenums_monthly_stats(self, trade):
        if trade.status == trade.Closed:
            curr_month_daterange_str = self.get_currentmonth_daterange()
            curr_month_arr = self.get_monthly_stats_entry(curr_month_daterange_str)
            curr_month_arr.total.closed += 1

            won = int(trade.pnlcomm >= 0.0)
            curr_month_arr.won.total += won

    def update_netprofit_monthly_stats(self):
        npd_list = list(self.netprofits_data.items())
        if len(npd_list) > 0:
            monthbegin_date = npd_list[0][0]
            monthbegin_equity_val = self.p.cash
            curr_equity_date = None
            curr_equity_val = self.p.cash
            for npd in npd_list:
                if curr_equity_date and self.check_next_month(monthbegin_date, npd[0]) is True:
                    monthbegin_date = npd[0]
                    monthbegin_equity_val = curr_equity_val

                curr_equity_date = npd[0]
                curr_equity_val += npd[1]

                monthly_pnl_pct = ((curr_equity_val - monthbegin_equity_val) * 100 / monthbegin_equity_val) if monthbegin_equity_val != 0 else 0
                curr_month_daterange_str = self.get_month_daterange(curr_equity_date)
                curr_month_arr = self.get_monthly_stats_entry(curr_month_daterange_str)
                curr_month_arr.pnl.netprofit.total = monthly_pnl_pct
        # Workaround: delete last element of self.rets.monthly_stats array - do not need to see last month of the whole calculation
        if len(self.rets.monthly_stats) > 0:
            self.rets.monthly_stats.popitem()

    def update_netprofits_data(self):
        trades = self.rets
        trades.total.netprofitsdata = self.get_netprofits_data()

    def print_debug_info(self):
        print("!!!!! self.netprofits_data={}\n".format(self.netprofits_data))
        print("All Trades:")
        npd_list = list(self.netprofits_data.items())
        prev_equity_val = self.p.cash
        curr_equity_val = self.p.cash
        for npd in npd_list:
            curr_equity_date = npd[0]
            curr_equity_val += npd[1]
            pnl_pct = ((curr_equity_val - prev_equity_val) * 100 / prev_equity_val) if prev_equity_val != 0 else 0
            print("Trade closed. Date = {}, Net Profit = {}, curr_equity_val = {}, Net Profit(Pnl %) = {}".format(curr_equity_date, npd[1], curr_equity_val, pnl_pct))
            prev_equity_val = curr_equity_val

        print("\n!!!!! self.rets.monthly_stats={}\n".format(self.rets.monthly_stats))
        for key, val in self.rets.monthly_stats.items():
            print("Month {}: pnl.netprofit.total={}, total.closed={}, won.total={}".format(key, val.pnl.netprofit.total, val.total.closed, val.won.total))

    def stop(self):
        self.update_netprofit_monthly_stats()
        self.update_netprofits_data()
        #self.print_debug_info()
        super(TVTradeAnalyzer, self).stop()
        self.rets._close()

    def next(self):
        #print('!! INSIDE next(): strategy.position.size={}, broker.get_value()={}, broker.get_cash()={}, data.open={}, data.close={}, datetime[0]={}'.format(self.strategy.position.size, self.strategy.broker.get_value(), self.strategy.broker.get_cash(), self.data.open[0], self.data.close[0], self.get_currentdate()))
        trades = self.rets
        if self.buyandholdcalcbegin is True:
            trades.total.buyandholdreturn = self.data.close[0] * self.buyandholdnumshares - self.buyandholdstartvalue
            trades.total.buyandholdreturnpct = 100 * trades.total.buyandholdreturn / self.buyandholdstartvalue

    def notify_trade(self, trade):
        if trade.justopened:
            #print('!! INSIDE notify_trade JUST OPENED trade={}, strategy.position.size={}, broker.get_value()={}, broker.get_cash()={}, data.open={}, data.close={}, datetime[0]={}\n'.format(trade, self.strategy.position.size, self.strategy.broker.get_value(), self.strategy.broker.get_cash(), self.data.open[0], self.data.close[0], self.get_currentdate()))
            # Trade just opened
            self.rets.total.total += 1
            self.rets.total.open += 1
            if self.buyandholdcalcbegin is False:
                self.buyandholdcalcbegin = True
                self.buyandholdnumshares = int(self.p.cash / trade.price)
                self.buyandholdstartvalue = self.buyandholdnumshares * trade.price         

        elif trade.status == trade.Closed:
            #print('!! INSIDE notify_trade CLOSED trade={}, broker.get_value()={}, data.open={}, data.close={}, datetime[0]={}\n'.format(trade, self.strategy.broker.get_value(), self.data.open[0], self.data.close[0], self.get_currentdate()))
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
            self.set_netprofit_value(trade.pnlcomm)
            self.update_tradenums_monthly_stats(trade)

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
