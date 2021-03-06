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
from montecarlo.montecarlo import MonteCarloSimulator
import pandas as pd
from model.linreg import LinearRegressionCalculator

__all__ = ['TVTradeAnalyzer']


class TVTradeAnalyzer(Analyzer):
    '''
    Modified version of Backtrader's TradeAnalyzer that calculates NetProfit, GrossProfit, GrossLoss, ProfitFactor, BuyAndHoldReturn values in the same way as in TradingView
    '''
    params = (
        ('cash', 0),
    )

    def create_analysis(self):
        self.mcsimulator = MonteCarloSimulator()
        self.rets = AutoOrderedDict()
        self.rets.total.total = 0
        self.rets.len.total = 0
        self.buyandholdcalcbegin = False
        self.buyandholdnumshares = 0
        self.buyandholdstartvalue = 0
        self.netprofits_data = AutoOrderedDict()
        self.skip_trade_update_flag = False

    def set_netprofit_value(self, value):
        self.netprofits_data[self.get_currentdate()] = value

    def get_equitycurve_data_dict(self):
        equity = 0
        result = {}
        for date, netprofit in self.netprofits_data.items():
            date_key = int(date.strftime('%y%m%d%H%M'))
            equity += netprofit
            result[date_key] = round(equity)
        return result

    def get_equitycurve_data_str(self):
        equity = 0
        result = {}
        for date, netprofit in self.netprofits_data.items():
            date_key = int(date.strftime('%y%m%d%H%M'))
            equity += netprofit
            result[date_key] = round(equity)
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

                monthly_pnl = curr_equity_val - monthbegin_equity_val
                monthly_pnl_pct = (monthly_pnl * 100 / monthbegin_equity_val) if monthbegin_equity_val != 0 else 0
                curr_month_daterange_str = self.get_month_daterange(curr_equity_date)
                curr_month_arr = self.get_monthly_stats_entry(curr_month_daterange_str)
                curr_month_arr.pnl.netprofit.total = monthly_pnl
                curr_month_arr.pnl.netprofit.pct = monthly_pnl_pct

    def update_equitycurve_data(self):
        trades = self.rets
        trades.total.equity.equitycurvedata = self.get_equitycurve_data_str()
        equity_curve_data_dict = self.get_equitycurve_data_dict()
        lr_stats = LinearRegressionCalculator.calculate(equity_curve_data_dict)
        trades.total.equity.stats.angle = lr_stats.angle
        trades.total.equity.stats.slope = lr_stats.slope
        trades.total.equity.stats.intercept = lr_stats.intercept
        trades.total.equity.stats.r_value = lr_stats.r_value
        trades.total.equity.stats.r_squared = lr_stats.r_squared
        trades.total.equity.stats.p_value = lr_stats.p_value
        trades.total.equity.stats.std_err = lr_stats.std_err

    def update_mcsimulation_data(self):
        trades = self.rets
        if self.netprofits_data and len(self.netprofits_data) > 0:
            netprofits_series = pd.Series(list(self.netprofits_data.values()))
            mcsimulation = self.mcsimulator.calculate(netprofits_series, self.p.cash)
            trades.total.mcsimulation.risk_of_ruin = mcsimulation.risk_of_ruin
            trades.total.mcsimulation.median_dd = mcsimulation.median_dd
            trades.total.mcsimulation.median_return = mcsimulation.median_return

    def update_processing_status(self, processing_status):
        trades = self.rets
        trades.processing_status = processing_status

    def update_sl_counts_data(self, is_tsl_flag):
        trades = self.rets
        trades.sl.count += 1 if is_tsl_flag is False else 0
        trades.tsl.count += 1 if is_tsl_flag is True else 0

    def update_moved_tsl_counts_data(self, is_tsl_flag):
        trades = self.rets
        trades.tsl.moved.count += 1 if is_tsl_flag is True else 0

    def update_tp_counts_data(self, is_ttp_flag):
        trades = self.rets
        trades.tp.count += 1 if is_ttp_flag is False else 0
        trades.ttp.count += 1 if is_ttp_flag is True else 0

    def update_moved_ttp_counts_data(self, is_ttp_flag):
        trades = self.rets
        trades.ttp.moved.count += 1 if is_ttp_flag is True else 0

    def update_tb_counts_data(self):
        trades = self.rets
        trades.tb.count += 1

    def update_moved_tb_counts_data(self):
        trades = self.rets
        trades.tb.moved.count += 1

    def update_dca_triggered_counts_data(self):
        trades = self.rets
        trades.dca.triggered.count += 1

    def update_bars_in_trades_ratio(self):
        trades = self.rets
        trades.len.tradebarsratio_pct = 100 * trades.len.total / trades.total.barsnumber

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
        print("Data in total.equity={}".format(vars(self.rets.total.equity)))

        print("\n!!!!! self.rets.monthly_stats={}\n".format(self.rets.monthly_stats))
        for key, val in self.rets.monthly_stats.items():
            print("Month {}: pnl.netprofit.total={}, pnl.netprofit.pct={}, total.closed={}, won.total={}".format(key, val.pnl.netprofit.total, val.pnl.netprofit.pct, val.total.closed, val.won.total))

    def stop(self):
        self.update_netprofit_monthly_stats()
        self.update_equitycurve_data()
        self.update_mcsimulation_data()
        #self.print_debug_info()
        super(TVTradeAnalyzer, self).stop()
        self.rets._close()

    def next(self):
        # self.strategy.log('!! TVTradeAnalyzer: INSIDE next(): strategy.position.size={}, broker.get_value()={}, broker.get_cash()={}, data.open={}, data.close={}, datetime[0]={}'.format(self.strategy.position.size, self.strategy.broker.get_value(), self.strategy.broker.get_cash(), self.data.open[0], self.data.close[0], self.get_currentdate()))
        trades = self.rets
        trades.total.barsnumber += 1
        self.update_bars_in_trades_ratio()
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
                self.buyandholdnumshares = self.p.cash / trade.price
                self.buyandholdstartvalue = self.buyandholdnumshares * trade.price         

        elif trade.status == trade.Closed:
            #print('!! INSIDE notify_trade CLOSED trade={}, broker.get_value()={}, data.open={}, data.close={}, datetime[0]={}\n'.format(trade, self.strategy.broker.get_value(), self.data.open[0], self.data.close[0], self.get_currentdate()))
            trades = self.rets

            res = AutoDict()
            # Trade just closed

            if not self.skip_trade_update_flag:
                won = res.won = int(trade.pnlcomm >= 0.0)
                lost = res.lost = int(not won)
                tlong = res.tlong = trade.long
                tshort = res.tshort = not trade.long

            trades.total.open -= 1
            trades.total.closed += 1

            if self.skip_trade_update_flag:
                return

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

            self.update_bars_in_trades_ratio()

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
