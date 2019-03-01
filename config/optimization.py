from enum import Enum
from optimization.filters import ValueFilter, TopNFilter, TopNPercentFilter, FilterSequence


class StrategyOptimizationEnum(Enum):
    STRATEGY_OPT_PARAMETER_NET_PROFIT_PCT = "Net Profit Pct"
    STRATEGY_OPT_PARAMETER_MAX_DRAWDOWN_PCT = "Max Drawdown Pct"
    STRATEGY_OPT_PARAMETER_MAX_DRAWDOWN_LENGTH = "Max Drawdown Length"
    STRATEGY_OPT_PARAMETER_WINNING_MONTHS_PCT = "Winning Months Pct"
    STRATEGY_OPT_PARAMETER_PROFIT_FACTOR = "Profit Factor"
    STRATEGY_OPT_PARAMETER_SQN = "SQN"


class StrategyOptimizationFactory(object):

    # Step 2 (Back testing) configuration
    _BKTEST_TOTAL_CLOSED_TRADES_VALUE_FILTER = ValueFilter("Total Closed Trades", 200, False)

    _BKTEST_MAX_DRAWDOWN_PCT_VALUE_FILTER = ValueFilter("Max Drawdown, %", -50, False)

    _BKTEST_NET_PROFIT_VALUE_FILTER = ValueFilter("Net Profit, %", 50, False)

    _BKTEST_EQUITY_CURVE_ANGLE_VALUE_FILTER = ValueFilter("Equity Curve Angle", 5, False)

    _BKTEST_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("Equity Curve R-value", 0.85, False)

    _BKTEST_MAX_DRAWDOWN_PCT_TOP_N_PCT_VALUE_FILTER = TopNPercentFilter("Max Drawdown, %", 25, False)

    _BKTEST_FILTERS = FilterSequence([_BKTEST_TOTAL_CLOSED_TRADES_VALUE_FILTER, _BKTEST_NET_PROFIT_VALUE_FILTER, _BKTEST_EQUITY_CURVE_ANGLE_VALUE_FILTER, _BKTEST_EQUITY_CURVE_R_VALUE_FILTER, _BKTEST_MAX_DRAWDOWN_PCT_TOP_N_PCT_VALUE_FILTER])


    # Step 4 (Forward testing) configuration
    _FWTEST_TOTAL_CLOSED_TRADES_VALUE_FILTER = ValueFilter("FwTest: Total Closed Trades", 20, False)

    _FWTEST_EQUITY_CURVE_ANGLE_VALUE_FILTER = ValueFilter("FwTest: Equity Curve Angle", 5, False)

    _FWTEST_EQUITY_CURVE_R_VALUE_FILTER = ValueFilter("FwTest: Equity Curve R-value", 0.8, False)

    _FWTEST_EQUITY_CURVE_R_VALUE_TOP_VALUE_FILTER = TopNFilter("FwTest: Equity Curve R-value", 1, False)

    _FWTEST_FILTERS = FilterSequence([_FWTEST_TOTAL_CLOSED_TRADES_VALUE_FILTER, _FWTEST_EQUITY_CURVE_ANGLE_VALUE_FILTER, _FWTEST_EQUITY_CURVE_R_VALUE_FILTER, _FWTEST_EQUITY_CURVE_R_VALUE_TOP_VALUE_FILTER])


    # Step5 testing configuration
    _STEP5_TOP_NET_PROFIT_VALUE_FILTER = TopNFilter("FwTest: Combined Net Profit", 1, False)


    @classmethod
    def get_filters_step2(cls):
        return cls._BKTEST_FILTERS

    @classmethod
    def get_filters_step4(cls):
        return cls._FWTEST_FILTERS

    @classmethod
    def get_filters_step5(cls):
        return cls._STEP5_TOP_NET_PROFIT_VALUE_FILTER

