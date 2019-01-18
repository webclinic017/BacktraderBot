from enum import Enum
from strategies.trendmas import AlexNoroTrendMAsStrategy
from strategies.sila import AlexNoroSILAStrategy
from strategies.fastrsi import AlexNoroRobotBitMEXFastRSIStrategy


class BTStrategy(object):
    c = None
    long_name = ""
    prefix_name = ""

    def __init__(self, cls, long_name, prefix_name):
        self.clazz = cls
        self.long_name = long_name
        self.prefix_name = prefix_name


class BTStrategyEnum(Enum):
    ALEX_NORO_TRENDMAS_STRATEGY_ID = BTStrategy(AlexNoroTrendMAsStrategy, "AlexNoroTrendMAsStrategy", "TrendMAs2_3")
    ALEX_NORO_SILA_STRATEGY_ID = BTStrategy(AlexNoroSILAStrategy, "AlexNoroSILAStrategy", "SILA1_6_1L")
    ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID = BTStrategy(AlexNoroRobotBitMEXFastRSIStrategy, "AlexNoroRobotBitMEXFastRSIStrategy", "robotFastRsi1_0")

    @classmethod
    def get_strategy_enum_by_str(cls, strategy_str):
        for name, member in BTStrategyEnum.__members__.items():
            if member.value.long_name == strategy_str:
                return member
