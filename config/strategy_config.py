from config.strategy_enum import BTStrategyEnum

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
            "takepercent": range(0, 5),
            "needbe": (False, True),
            "needct": (False, True),
            "bodylen": range(0, 13, 3),
            "trb": range(1, 5),
            "len": 20,
        },
        BTStrategyEnum.S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID: {
            "needlong": (False, True),
            "needshort": (False, True),
            "leverage": 1,
            "accuracy": range(1, 11),
            "isreversive": (False, True),
        },
        BTStrategyEnum.S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID: {
            "needlong": (False, True),
            "needshort": (False, True),
            "length": 20,
            "mult": 2.0,
            "lengthKC": 20,
            "multKC": 1.5,
            "usecolor": (False, True),
            "usebody": (False, True),
        },
        BTStrategyEnum.S007_ALEX_NORO_MULTIMA_STRATEGY_ID: {
            "needlong": (False, True),
            "needshort": (False, True),
            "usema1": True,
            "usema2": True,
            "lenma1": (10, 20, 40, 80, 100, 120, 150, 180, 200),
            "lenma2": (10, 20, 40, 80, 100, 120, 150, 180, 200),
            "usecf": (False, True),
        },
        BTStrategyEnum.S008_ALEX_NORO_SUPERTREND_STRATEGY_ID: {
            "needlong": (False, True),
            "needshort": (False, True),
            "cloud": 25,
            "Factor": range(1, 11),
            "ATR": 7,
        },
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
        },
        BTStrategyEnum.S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID: {
            "needlong": False,
            "needshort": False,
            "leverage": 0,
            "accuracy": 0,
            "isreversive": False,
        },
        BTStrategyEnum.S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID: {
            "needlong": False,
            "needshort": False,
            "length": 0,
            "mult": 0,
            "lengthKC": 0,
            "multKC": 0,
            "usecolor": False,
            "usebody": False,
        },
        BTStrategyEnum.S007_ALEX_NORO_MULTIMA_STRATEGY_ID: {
            "needlong": False,
            "needshort": False,
            "usema1": False,
            "usema2": False,
            "lenma1": 0,
            "lenma2": 0,
            "usecf": False,
        },
        BTStrategyEnum.S008_ALEX_NORO_SUPERTREND_STRATEGY_ID: {
            "needlong": False,
            "needshort": False,
            "cloud": 0,
            "Factor": 0,
            "ATR": 0,
        },
    }

    _DEBUG_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "needstops": False,
            "stoppercent": 5,
            "usefastsma": True,
            "fastlen": 5,
            "slowlen": 17,
            "bars": 2,
            "needex": False,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 6,
            "tomonth": 12,
            "fromday": 1,
            "today": 31,
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
            "frommonth": 6,
            "tomonth": 12,
            "fromday": 1,
            "today": 31,
        },
        BTStrategyEnum.S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID: {
            "needlong": True,
            "needshort": False,
            "rsiperiod": 7,
            "rsibars": 1,
            "rsilong": 30,
            "rsishort": 70,
            "useocf": True,
            "useccf": True,
            "openbars": 3,
            "closebars": 3,
            "useobf": True,
            "usecbf": True,
            "openbody": 20,
            "closebody": 50,
            "fromyear": 2017,
            "toyear": 2018,
            "frommonth": 1,
            "tomonth": 6,
            "fromday": 1,
            "today": 30,
        },
        BTStrategyEnum.S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "takepercent": 1,
            "needbe": True,
            "needct": True,
            "bodylen": 10,
            "trb": 5,
            "len": 20,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 10,
            "tomonth": 10,
            "fromday": 1,
            "today": 31,
        },
        BTStrategyEnum.S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "leverage": 1,
            "accuracy": 1,
            "isreversive": False,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 11,
            "tomonth": 11,
            "fromday": 1,
            "today": 30,
        },
        BTStrategyEnum.S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "length": 20,
            "mult": 2.0,
            "lengthKC": 20,
            "multKC": 1.5,
            "usecolor": True,
            "usebody": True,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 10,
            "tomonth": 10,
            "fromday": 1,
            "today": 31,
        },
        BTStrategyEnum.S007_ALEX_NORO_MULTIMA_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "usema1": True,
            "usema2": True,
            "lenma1": 20,
            "lenma2": 30,
            "usecf": True,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 10,
            "tomonth": 10,
            "fromday": 1,
            "today": 31,
        },
        BTStrategyEnum.S008_ALEX_NORO_SUPERTREND_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "cloud": 25,
            "Factor": 10,
            "ATR": 7,
            "fromyear": 2018,
            "toyear": 2018,
            "frommonth": 2,
            "tomonth": 8,
            "fromday": 1,
            "today": 31,
        },
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
