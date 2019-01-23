from enum import Enum
from strategies.trendmas import S001_AlexNoroTrendMAsStrategy
from strategies.sila import S002_AlexNoroSILAStrategy
from strategies.fastrsi import S003_AlexNoroRobotBitMEXFastRSIStrategy
from strategies.bands import S004_AlexNoroBandsScalperStrategy


class BTStrategy(object):
    c = None
    long_name = ""
    prefix_name = ""

    def __init__(self, cls, long_name, prefix_name):
        self.clazz = cls
        self.long_name = long_name
        self.prefix_name = prefix_name


class BTStrategyEnum(Enum):
    S001_ALEX_NORO_TRENDMAS_STRATEGY_ID = BTStrategy(S001_AlexNoroTrendMAsStrategy, "S001_AlexNoroTrendMAsStrategy", "S001_TrendMAs2_3")
    S002_ALEX_NORO_SILA_STRATEGY_ID = BTStrategy(S002_AlexNoroSILAStrategy, "S002_AlexNoroSILAStrategy", "S002_SILA1_6_1L")
    S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID = BTStrategy(S003_AlexNoroRobotBitMEXFastRSIStrategy, "S003_AlexNoroRobotBitMEXFastRSIStrategy", "S003_RobotFastRsi1_0")
    S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID = BTStrategy(S004_AlexNoroBandsScalperStrategy, "S004_AlexNoroBandsScalperStrategy", "S004_BandsScalper1_6")

    @classmethod
    def get_strategy_enum_by_str(cls, strategy_str):
        for name, member in BTStrategyEnum.__members__.items():
            if member.value.long_name == strategy_str:
                return member
