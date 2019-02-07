from enum import Enum


class StrategyOptimizationEnum(Enum):
    STRATEGY_OPT_PARAMETER_BALANCE = "Balance"
    STRATEGY_OPT_PARAMETER_PROFIT_FACTOR = "Profit Factor"
    STRATEGY_OPT_PARAMETER_MAXIMAL_DRAWDOWN = "Maximal Drawdown"
