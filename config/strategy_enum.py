from enum import Enum
from strategies.S001_trendmas import S001_AlexNoroTrendMAsStrategy
from strategies.S002_sila import S002_AlexNoroSILAStrategy
from strategies.S003_fastrsi import S003_AlexNoroRobotBitMEXFastRSIStrategy
from strategies.S004_bands import S004_AlexNoroBandsScalperStrategy
from strategies.S005_triplersi import S005_AlexNoroTripleRSIStrategy
from strategies.S006_sqmomentum import S006_AlexNoroSqueezeMomentumStrategy
from strategies.S007_multima import S007_AlexNoroMultimaStrategy
from strategies.S008_supertrend import S008_AlexNoroSuperTrendStrategy


class BTStrategy(object):
    c = None
    long_name = ""
    prefix_name = ""

    def __init__(self, cls, long_name):
        self.clazz = cls
        self.long_name = long_name


class BTStrategyEnum(Enum):
    S001_ALEX_NORO_TRENDMAS_STRATEGY_ID = BTStrategy(S001_AlexNoroTrendMAsStrategy, "S001_AlexNoroTrendMAsStrategy")
    S002_ALEX_NORO_SILA_STRATEGY_ID = BTStrategy(S002_AlexNoroSILAStrategy, "S002_AlexNoroSILAStrategy")
    S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID = BTStrategy(S003_AlexNoroRobotBitMEXFastRSIStrategy, "S003_AlexNoroRobotBitMEXFastRSIStrategy")
    S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID = BTStrategy(S004_AlexNoroBandsScalperStrategy, "S004_AlexNoroBandsScalperStrategy")
    S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID = BTStrategy(S005_AlexNoroTripleRSIStrategy, "S005_AlexNoroTripleRSIStrategy")
    S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID = BTStrategy(S006_AlexNoroSqueezeMomentumStrategy, "S006_AlexNoroSqueezeMomentumStrategy")
    S007_ALEX_NORO_MULTIMA_STRATEGY_ID = BTStrategy(S007_AlexNoroMultimaStrategy, "S007_AlexNoroMultimaStrategy")
    S008_ALEX_NORO_SUPERTREND_STRATEGY_ID = BTStrategy(S008_AlexNoroSuperTrendStrategy, "S008_AlexNoroSuperTrendStrategy")

    @classmethod
    def get_strategy_enum_by_str(cls, strategy_str):
        for name, member in BTStrategyEnum.__members__.items():
            if member.value.long_name == strategy_str:
                return member
