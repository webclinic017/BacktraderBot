from enum import Enum
from optimization.filters import ValueFilter, TopNPercentFilter, CombinedResultsMergingFilter, FilterSequence


class StrategyOptimizationEnum(Enum):
    STRATEGY_OPT_PARAMETER_NET_PROFIT_PCT = "Net Profit Pct"
    STRATEGY_OPT_PARAMETER_MAX_DRAWDOWN_PCT = "Max Drawdown Pct"
    STRATEGY_OPT_PARAMETER_MAX_DRAWDOWN_LENGTH = "Max Drawdown Length"
    STRATEGY_OPT_PARAMETER_WINNING_MONTHS_PCT = "Winning Months Pct"
    STRATEGY_OPT_PARAMETER_PROFIT_FACTOR = "Profit Factor"
    STRATEGY_OPT_PARAMETER_SQN = "SQN"
    STRATEGY_OPT_PARAMETER_SHARPE_RATIO = "Sharpe Ratio"


class StrategyOptimizationFactory(object):

    _COMBINED_RESULTS_MERGING_FILTER = CombinedResultsMergingFilter([
        TopNPercentFilter("Net Profit, %", 10, False),
        TopNPercentFilter("Max Drawdown, %", 10, False),
        TopNPercentFilter("Max Drawdown Length", 10, True),
        #TopNPercentFilter("Winning Months, %", 10, False),
        TopNPercentFilter("Profit Factor", 10, False),
        TopNPercentFilter("SQN", 10, False),
        #TopNPercentFilter("Sharpe Ratio", 10, False)
    ])

    _TOTAL_CLOSED_TRADES_VALUE_FILTER = ValueFilter("Total Closed Trades", 100, False)

    _NET_PROFIT_VALUE_FILTER = ValueFilter("Net Profit, %", 20, False)

    _SQN_VALUE_FILTER = ValueFilter("SQN", 0.5, False)

    _ALL_FILTERS = FilterSequence([_TOTAL_CLOSED_TRADES_VALUE_FILTER, _NET_PROFIT_VALUE_FILTER, _SQN_VALUE_FILTER, _COMBINED_RESULTS_MERGING_FILTER])

    @classmethod
    def create_filters(cls):
        return cls._ALL_FILTERS

