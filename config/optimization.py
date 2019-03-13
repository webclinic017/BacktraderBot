from enum import Enum
from optimization.filters import ValueFilter, TopNFilter, TopNPercentFilter, FilterSequence, GroupByConditionalFilter, GroupByCombinationsFilter


class StrategyOptimizationEnum(Enum):
    STRATEGY_OPT_PARAMETER_NET_PROFIT_PCT = "Net Profit Pct"
    STRATEGY_OPT_PARAMETER_MAX_DRAWDOWN_PCT = "Max Drawdown Pct"
    STRATEGY_OPT_PARAMETER_MAX_DRAWDOWN_LENGTH = "Max Drawdown Length"
    STRATEGY_OPT_PARAMETER_WINNING_MONTHS_PCT = "Winning Months Pct"
    STRATEGY_OPT_PARAMETER_PROFIT_FACTOR = "Profit Factor"
    STRATEGY_OPT_PARAMETER_SQN = "SQN"


class StrategyOptimizationFactory(object):

    # Step 2 (Back testing) configuration
    _STEP2_TOTAL_CLOSED_TRADES_VALUE_FILTER = ValueFilter("Total Closed Trades", 100, False)

    _STEP2_NET_PROFIT_TO_MAXDD_VALUE_FILTER = ValueFilter("Net Profit To Max Drawdown", 1.0, False)

    _STEP2_MAX_DRAWDOWN_PCT_VALUE_FILTER = ValueFilter("Max Drawdown, %", -30, False)

    _STEP2_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("Equity Curve R-value", 0.7, False)

    _STEP2_MAIN_FILTER_PART = FilterSequence([_STEP2_NET_PROFIT_TO_MAXDD_VALUE_FILTER, _STEP2_TOTAL_CLOSED_TRADES_VALUE_FILTER, _STEP2_MAX_DRAWDOWN_PCT_VALUE_FILTER, _STEP2_EQUITY_CURVE_R_VALUE_FILTER])

    _STEP2_FILTERS = GroupByConditionalFilter(
        ["Strategy ID", "Currency Pair"],
        _STEP2_MAIN_FILTER_PART,
    )

    # Step 4 (Forward testing) configuration
    _STEP4_TOTAL_CLOSED_TRADES_VALUE_FILTER = ValueFilter("FwTest: Total Closed Trades", 60, False)

    _STEP4_NET_PROFIT_VALUE_FILTER = ValueFilter("FwTest: Net Profit, %", 1, False)

    _STEP4_NET_PROFIT_TO_MAXDD_VALUE_FILTER = ValueFilter("FwTest: Net Profit To Max Drawdown", 0.4, False)

    _STEP4_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("FwTest: Equity Curve R-value", 0.7, False)

    _STEP4_COMBINED_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("FwTest: Combined Equity Curve R-value", 0.8, False)

    _STEP4_COMBINED_NET_PROFIT_TOPNPCT_FILTER = TopNPercentFilter("FwTest: Combined Net Profit", 30, False)

    _STEP4_MAIN_FILTER_PART = FilterSequence([_STEP4_TOTAL_CLOSED_TRADES_VALUE_FILTER, _STEP4_NET_PROFIT_VALUE_FILTER, _STEP4_NET_PROFIT_TO_MAXDD_VALUE_FILTER, _STEP4_EQUITY_CURVE_R_VALUE_FILTER, _STEP4_COMBINED_EQUITY_CURVE_R_VALUE_FILTER, _STEP4_COMBINED_NET_PROFIT_TOPNPCT_FILTER])

    _STEP4_FILTERS = GroupByConditionalFilter(
        ["Strategy ID", "Currency Pair"],
        _STEP4_MAIN_FILTER_PART,
    )


    # Step5 configuration
    _STEP5_GROUPBY_FILTER = GroupByCombinationsFilter(
        ["Currency Pair"],
        ["FwTest: Combined Net Profit"]#, "FwTest: Equity Curve R-value", "FwTest: Combined Equity Curve R-value"],
    )

    _STEP5_FILTERS = FilterSequence([_STEP5_GROUPBY_FILTER])

    @classmethod
    def get_filters_step2(cls):
        return cls._STEP2_FILTERS

    @classmethod
    def get_filters_step4(cls):
        return cls._STEP4_FILTERS

    @classmethod
    def get_filters_step5(cls):
        return cls._STEP5_FILTERS

