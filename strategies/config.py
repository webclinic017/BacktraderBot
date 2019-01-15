from strategies.strategy import BTStrategyEnum

class BTStrategyConfig(object):

    _STEP1_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.ALEX_NORO_TRENDMAS_STRATEGY_ID: {
            "needlong": (False, True),
            "needshort": (False, True),
            "needstops": False,
            "stoppercent": 5,
            "usefastsma": True,
            "fastlen": range(3, 6),
            "slowlen": range(10, 27),
            "bars": range(0, 3),
            "needex": False
        },
        BTStrategyEnum.ALEX_NORO_SILA_STRATEGY_ID: {
            "sensup": range(0, 9),
            "sensdn": range(0, 9),
            "usewow": True,
            "usebma": True,
            "usebc": True,
            "usest": True,
            "usedi": True,
            "usetts": True,
            "usersi": True,
            "usewto": True,
            "uselocoentry": (False, True),
        },
    }

    _STEP3_STRATEGY_DEFAULT_PARAMS_DICT = {
        BTStrategyEnum.ALEX_NORO_TRENDMAS_STRATEGY_ID: {
            "needlong": False,
            "needshort": False,
            "needstops": False,
            "stoppercent": 0,
            "usefastsma": False,
            "fastlen": 0,
            "slowlen": 0,
            "bars": 0,
            "needex": False
        },
        BTStrategyEnum.ALEX_NORO_SILA_STRATEGY_ID: {
            "sensup": 0,
            "sensdn": 0,
            "usewow": False,
            "usebma": False,
            "usebc": False,
            "usest": False,
            "usedi": False,
            "usetts": False,
            "usersi": False,
            "usewto": False,
            "uselocoentry": False,
        },
    }

    @classmethod
    def get_step1_strategy_params(cls, strategy_enum):
        return cls._STEP1_STRATEGY_PARAMS_DICT[strategy_enum]

    @classmethod
    def get_step3_strategy_params(cls, strategy_enum):
        return cls._STEP3_STRATEGY_DEFAULT_PARAMS_DICT[strategy_enum]