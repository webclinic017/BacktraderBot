from config.strategy_enum import BTStrategyEnum


class AppConfig(object):

    _GLOBAL_STRATEGY_PARAMS_DICT = {
            "DEFAULT_START_CASH_VALUE": 1500,
            "DEFAULT_LOT_SIZE": 1470,
            "DEFAULT_LOT_TYPE": "Fixed",
            "STEP1_ENABLE_FILTERING": True,
            "STEP2_ENABLE_FILTERING": True,
            "STEP4_ENABLE_FILTERING": True,
            "STEP5_ENABLE_FILTERING": True,
            "STEP2_ENABLE_EQUITYCURVE_IMG_GENERATION": False,
            "STEP4_ENABLE_EQUITYCURVE_IMG_GENERATION": False,
        }

    _STEP1_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: {
            "needlong": (True, False),
            "needshort": (True, False),
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
            "needlong": (True, False),
            "needshort": (True, False),
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
            "needlong": (True, False),
            "needshort": (True, False),
            "takepercent": range(0, 5),
            "needbe": (False, True),
            "needct": (False, True),
            "bodylen": range(0, 13, 3),
            "trb": range(1, 5),
            "len": 20,
        },
        BTStrategyEnum.S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID: {
            "needlong": (True, False),
            "needshort": (True, False),
            "leverage": 1,
            "indi": (2, 3),
            "accuracy": range(1, 11),
            "isreversive": (False, True),
        },
        BTStrategyEnum.S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID: {
            "needlong": (True, False),
            "needshort": (True, False),
            "length": 20,
            "mult": 2.0,
            "lengthKC": 20,
            "multKC": 1.5,
            "usecolor": (False, True),
            "usebody": (False, True),
        },
        BTStrategyEnum.S007_ALEX_NORO_MULTIMA_STRATEGY_ID: {
            "needlong": (True, False),
            "needshort": (True, False),
            "usema1": True,
            "usema2": True,
            "lenma1": (10, 20, 40, 80, 100, 120, 150, 180, 200),
            "lenma2": (10, 20, 40, 80, 100, 120, 150, 180, 200),
            "usecf": (False, True),
        },
        BTStrategyEnum.S008_ALEX_NORO_SUPERTREND_STRATEGY_ID: {
            "needlong": (True, False),
            "needshort": (True, False),
            "cloud": 25,
            "Factor": range(1, 11),
            "ATR": 7,
        },
    }

    _DEBUG_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "1h",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },
            {
                "needlong": True,
                "needshort": False,
                "needstops": False,
                "stoppercent": 5,
                "usefastsma": True,
                "fastlen": 4,
                "slowlen": 21,
                "bars": 1,
                "needex": False,
                "fromyear": 2014,
                "toyear": 2017,
                "frommonth": 1,
                "tomonth": 6,
                "fromday": 1,
                "today": 30,
            }
        ],
        BTStrategyEnum.S002_ALEX_NORO_SILA_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 98000,
                "lottype": "Fixed"
            },
            {
                "sensup": 0,
                "sensdn": 7,
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
                "frommonth": 5,
                "tomonth": 6,
                "fromday": 1,
                "today": 30,
            }],
        BTStrategyEnum.S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 98000,
                "lottype": "Fixed"
            },
            {
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
                "closebody": 35,
                "fromyear": 2017,
                "toyear": 2018,
                "frommonth": 1,
                "tomonth": 6,
                "fromday": 1,
                "today": 30,
            }],
        BTStrategyEnum.S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 98000,
                "lottype": "Fixed"
            },
            {
                "needlong": True,
                "needshort": True,
                "takepercent": 4,
                "needbe": False,
                "needct": True,
                "bodylen": 12,
                "trb": 2,
                "len": 20,
                "fromyear": 2017,
                "toyear": 2018,
                "frommonth": 1,
                "tomonth": 6,
                "fromday": 1,
                "today": 30,
            }],
        BTStrategyEnum.S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 98000,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": True,
                "leverage": 1,
                "indi": 3,
                "accuracy": 5,
                "isreversive": True,
                "fromyear": 2018,
                "toyear": 2018,
                "frommonth": 1,
                "tomonth": 12,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "3h",
                "startcash": 18255,
                "lotsize": 1500,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": True,
                "length": 20,
                "mult": 2.0,
                "lengthKC": 20,
                "multKC": 1.5,
                "usecolor": False,
                "usebody": False,
                "fromyear": 2018,
                "toyear": 2019,
                "frommonth": 8,
                "tomonth": 2,
                "fromday": 1,
                "today": 28,
            }],
        BTStrategyEnum.S007_ALEX_NORO_MULTIMA_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 98000,
                "lottype": "Fixed"
            },  {
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
            }],
        BTStrategyEnum.S008_ALEX_NORO_SUPERTREND_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSDT",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 98000,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": False,
                "cloud": 25,
                "Factor": 10,
                "ATR": 7,
                "fromyear": 2017,
                "toyear": 2018,
                "frommonth": 7,
                "tomonth": 6,
                "fromday": 1,
                "today": 30,
            }],
    }

    @classmethod
    def get_global_default_cash_size(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["DEFAULT_START_CASH_VALUE"]

    @classmethod
    def get_global_lot_size(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["DEFAULT_LOT_SIZE"]

    @classmethod
    def get_global_lot_type(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["DEFAULT_LOT_TYPE"]

    @classmethod
    def is_global_step1_enable_filtering(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["STEP1_ENABLE_FILTERING"]

    @classmethod
    def is_global_step2_enable_filtering(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["STEP2_ENABLE_FILTERING"]

    @classmethod
    def is_global_step4_enable_filtering(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["STEP4_ENABLE_FILTERING"]

    @classmethod
    def is_global_step5_enable_filtering(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["STEP5_ENABLE_FILTERING"]

    @classmethod
    def is_global_step2_enable_equitycurve_img_generation(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["STEP2_ENABLE_EQUITYCURVE_IMG_GENERATION"]

    @classmethod
    def is_global_step4_enable_equitycurve_img_generation(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["STEP4_ENABLE_EQUITYCURVE_IMG_GENERATION"]

    @classmethod
    def get_step1_strategy_params(cls, strategy_enum):
        return cls._STEP1_STRATEGY_PARAMS_DICT[strategy_enum]

    @classmethod
    def get_debug_strategy_params(cls, strategy_enum):
        return cls._DEBUG_STRATEGY_PARAMS_DICT[strategy_enum]
