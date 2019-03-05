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
    _STEP2_TOTAL_CLOSED_TRADES_VALUE_FILTER = ValueFilter("Total Closed Trades", 200, False)

    _STEP2_MAX_DRAWDOWN_PCT_VALUE_FILTER = ValueFilter("Max Drawdown, %", -50, False)

    _STEP2_NET_PROFIT_VALUE_FILTER = ValueFilter("Net Profit, %", 50, False)

    _STEP2_EQUITY_CURVE_ANGLE_VALUE_FILTER = ValueFilter("Equity Curve Angle", 5, False)

    _STEP2_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("Equity Curve R-value", 0.85, False)

    _STEP2_MAX_DRAWDOWN_PCT_TOP_N_PCT_VALUE_FILTER = TopNPercentFilter("Max Drawdown, %", 25, False)

    _STEP2_MAIN_FILTER_PART = FilterSequence([_STEP2_TOTAL_CLOSED_TRADES_VALUE_FILTER, _STEP2_MAX_DRAWDOWN_PCT_VALUE_FILTER, _STEP2_NET_PROFIT_VALUE_FILTER, _STEP2_EQUITY_CURVE_ANGLE_VALUE_FILTER,
                                                _STEP2_EQUITY_CURVE_R_VALUE_FILTER, _STEP2_MAX_DRAWDOWN_PCT_TOP_N_PCT_VALUE_FILTER])

    _STEP2_ALTERNATIVE_FILTER_PART = TopNPercentFilter("Net Profit, %", 20, False)

    _STEP2_FILTERS = GroupByConditionalFilter(
        ["Strategy ID", "Currency Pair"],
        _STEP2_MAIN_FILTER_PART,
        _STEP2_ALTERNATIVE_FILTER_PART
    )

    # Step 4 (Forward testing) configuration
    _STEP4_TOTAL_CLOSED_TRADES_VALUE_FILTER = ValueFilter("FwTest: Total Closed Trades", 20, False)

    _STEP4_EQUITY_CURVE_ANGLE_VALUE_FILTER = ValueFilter("FwTest: Equity Curve Angle", 5, False)

    _STEP4_FROM_STEP2_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("Equity Curve R-value", 0.85, False)

    _STEP4_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("FwTest: Equity Curve R-value", 0.7, False)

    _STEP4_MAIN_FILTER_PART = FilterSequence([_STEP4_TOTAL_CLOSED_TRADES_VALUE_FILTER, _STEP4_EQUITY_CURVE_ANGLE_VALUE_FILTER, _STEP4_FROM_STEP2_EQUITY_CURVE_R_VALUE_FILTER, _STEP4_EQUITY_CURVE_R_VALUE_FILTER])

    _STEP4_ALTERNATIVE_FILTER_PART = TopNPercentFilter("FwTest: Combined Net Profit", 20, False)

    _STEP4_FILTERS = GroupByConditionalFilter(
        ["Strategy ID", "Currency Pair"],
        _STEP4_MAIN_FILTER_PART,
        _STEP4_ALTERNATIVE_FILTER_PART
    )


    # Step5 configuration
    _STEP5_FILTERS = GroupByCombinationsFilter(
        ["Currency Pair"],
        ["Net Profit", "Avg Monthly Net Profit, %", "Max Drawdown, %", "Win Rate, %", "Winning Months, %", "Profit Factor", "SQN", "Equity Curve Angle",
         "Equity Curve R-value", "FwTest: Net Profit", "FwTest: Avg Monthly Net Profit, %", "FwTest: Max Drawdown, %", "FwTest: Win Rate, %", "FwTest: Winning Months, %",
         "FwTest: Profit Factor", "FwTest: SQN", "FwTest: Equity Curve Angle", "FwTest: Equity Curve R-value", "FwTest: Combined Net Profit", "FwTest: Combined Equity Curve Angle", "FwTest: Combined Equity Curve R-value"],
        [False, True]
    )


    @classmethod
    def get_filters_step2(cls):
        return cls._STEP2_FILTERS

    @classmethod
    def get_filters_step4(cls):
        return cls._STEP4_FILTERS

    @classmethod
    def get_filters_step5(cls):
        return cls._STEP5_FILTERS

