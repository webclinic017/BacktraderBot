from strategies.strategy import BTStrategyEnum

class BTStrategyConfig(object):

    _STEP1_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: {
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
        BTStrategyEnum.S002_ALEX_NORO_SILA_STRATEGY_ID: {
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
        BTStrategyEnum.S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID: {
            "needlong": (False, True),
            "needshort": (False, True),
            "rsiperiod": 7,
            "rsibars": range(1, 5),
            "rsilong": 30, #range(15, 31, 3),
            "rsishort": 70, #range(70, 86, 3),
            "useocf": True,
            "useccf": True,
            "openbars": range(1, 4),
            "closebars": range(1, 4),
            "useobf": True,
            "usecbf": True,
            "openbody": 20,
            "closebody": range(20, 51, 5),
        },
        BTStrategyEnum.S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID: {
            "needlong": (False, True),
            "needshort": (False, True),
            "takepercent": range(0, 4),
            "needbe": (False, True),
            "needct": (False, True),
            "bodylen": range(0, 16, 3),
            "trb": range(1, 6),
            "len": range(15, 28, 3),
        }
    }

    _STEP3_STRATEGY_DEFAULT_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: {
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
        BTStrategyEnum.S002_ALEX_NORO_SILA_STRATEGY_ID: {
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
        BTStrategyEnum.S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID: {
            "needlong": False,
            "needshort": False,
            "rsiperiod": 0,
            "rsibars": 0,
            "rsilong": 0,
            "rsishort": 0,
            "useocf": False,
            "useccf": False,
            "openbars": 0,
            "closebars": 0,
            "useobf": False,
            "usecbf": False,
            "openbody": 0,
            "closebody": 0,
        },
        BTStrategyEnum.S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID: {
            "needlong": False,
            "needshort": False,
            "takepercent": 0,
            "needbe": False,
            "needct": False,
            "bodylen": 0,
            "trb": 0,
            "len": 0,
        }
    }

    _DEBUG_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "needstops": False,
            "stoppercent": 5,
            "usefastsma": True,
            "fastlen": 3,
            "slowlen": 17,
            "bars": 2,
            "needex": False,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 11,
            "tomonth": 11,
            "fromday": 1,
            "today": 30,
        },
        BTStrategyEnum.S002_ALEX_NORO_SILA_STRATEGY_ID: {
            "sensup": 0,
            "sensdn": 0,
            "usewow": True,
            "usebma": True,
            "usebc": True,
            "usest": True,
            "usedi": True,
            "usetts": True,
            "usersi": True,
            "usewto": True,
            "uselocoentry": False,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 11,
            "tomonth": 11,
            "fromday": 1,
            "today": 30,
        },
        BTStrategyEnum.S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID: {
            "needlong": False,
            "needshort": True,
            "rsiperiod": 7,
            "rsibars": 4,
            "rsilong": 30,
            "rsishort": 70,
            "useocf": True,
            "useccf": True,
            "openbars": 3,
            "closebars": 2,
            "useobf": True,
            "usecbf": True,
            "openbody": 20,
            "closebody": 20,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 3,
            "tomonth": 3,
            "fromday": 1,
            "today": 31,
        },
        BTStrategyEnum.S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "takepercent": 0,
            "needbe": True,
            "needct": False,
            "bodylen": 10,
            "trb": 1,
            "len": 20,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 10,
            "tomonth": 10,
            "fromday": 1,
            "today": 31,
        }
    }

    @classmethod
    def get_step1_strategy_params(cls, strategy_enum):
        return cls._STEP1_STRATEGY_PARAMS_DICT[strategy_enum]

    @classmethod
    def get_step3_strategy_params(cls, strategy_enum):
        return cls._STEP3_STRATEGY_DEFAULT_PARAMS_DICT[strategy_enum]

    @classmethod
    def get_debug_strategy_params(cls, strategy_enum):
        return cls._DEBUG_STRATEGY_PARAMS_DICT[strategy_enum]
