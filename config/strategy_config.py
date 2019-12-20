from config.strategy_enum import BTStrategyEnum


class AppConfig(object):

    _GLOBAL_STRATEGY_PARAMS_DICT = {
            "DEFAULT_START_CASH_VALUE": 1500,
            "DEFAULT_LOT_SIZE": 1470,
            "DEFAULT_LOT_TYPE": "Fixed",
            "STEP1_ENABLE_FILTERING": False,
            "STEP2_ENABLE_FILTERING": False,
            "STEP4_ENABLE_FILTERING": True,
            "STEP5_ENABLE_FILTERING": True,
            "STEP2_ENABLE_EQUITYCURVE_IMG_GENERATION": False,
            "STEP4_ENABLE_EQUITYCURVE_IMG_GENERATION": True,
            "DRAW_EQUITYCURVE_IMG_X_AXIS_TRADES": True,    # True: generating equity curve images with number of closed trades as x-axis, False: otherwise use closed trade dates as x-axis
        }

    _DEFAULT_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSD",
                "timeframe": "1h",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },
            {
                "needlong": True,
                "needshort": True,
                "usefastsma": True,
                "fastlen": 5,
                "slowlen": 10,
                "bars": 1,
                "needex": False,
                "sl": 0,
                "tslflag": False,
                "tp": 14,
                "ttpdist": 0,
                "tbdist": 0,
                "numdca": 2,
                "dcainterval": 2,
                "dcasltimeout": 4,
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
                "currency_pair": "BTCUSD",
                "timeframe": "1h",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },
            {
                "needlong": True,
                "needshort": True,
                "sensup": 5,
                "sensdn": 5,
                "usewow": True,
                "usebma": True,
                "usebc": True,
                "usest": True,
                "usedi": True,
                "usetts": True,
                "usersi": True,
                "usewto": True,
                "uselocoentry": False,
                "sl": 4,
                "tslflag": False,
                "tp": 2,
                "ttpdist": 0,
                "tbdist": 0,
                "numdca": 2,
                "dcainterval": 1,
                "dcasltimeout": 0,
                "fromyear": 2019,
                "toyear": 2019,
                "frommonth": 2,
                "tomonth": 5,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "XRPUSD",
                "timeframe": "1h",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },
            {
                "needlong": True,
                "needshort": True,
                "rsiperiod": 7,
                "rsibars": 2,
                "rsilong": 30,
                "rsishort": 70,
                "useocf": True,
                "useccf": True,
                "openbars": 1,
                "closebars": 1,
                "useobf": True,
                "usecbf": True,
                "openbody": 20,
                "closebody": 20,
                "sl": 2,
                "tslflag": True,
                "tp": 2,
                "ttpdist": 1,
                "tbdist": 1,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
                "fromyear": 2017,
                "toyear": 2018,
                "frommonth": 8,
                "tomonth": 7,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSD",
                "timeframe": "15m",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },
            {
                "needlong": True,
                "needshort": True,
                "takepercent": 0,
                "needbe": False,
                "needct": False,
                "bodylen": 3,
                "trb": 3,
                "len": 20,
                "sl": 0,
                "tslflag": False,
                "tp": 4,
                "ttpdist": 0,
                "tbdist": 0,
                "numdca": 0,
                "dcainterval": 0,
                "dcasltimeout": 0,
                "fromyear": 2019,
                "toyear": 2019,
                "frommonth": 2,
                "tomonth": 5,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "XRPUSD",
                "timeframe": "1h",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": True,
                "leverage": 1,
                "indi": 2,
                "accuracy": 4,
                "isreversive": True,
                "sl": 2,
                "tslflag": True,
                "tp": 2,
                "ttpdist": 1,
                "tbdist": 1,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
                "fromyear": 2017,
                "toyear": 2018,
                "frommonth": 8,
                "tomonth": 7,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSD",
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
                "sl": 2,
                "tslflag": True,
                "tp": 2,
                "ttpdist": 1,
                "tbdist": 1,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
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
                "currency_pair": "XRPUSD",
                "timeframe": "1h",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": True,
                "usema1": True,
                "usema2": True,
                "lenma1": 100,
                "lenma2": 100,
                "usecf": True,
                "sl": 2,
                "tslflag": True,
                "tp": 2,
                "ttpdist": 1,
                "tbdist": 1,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
                "fromyear": 2018,
                "toyear": 2018,
                "frommonth": 2,
                "tomonth": 7,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S008_ALEX_NORO_SUPERTREND_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSD",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 10000,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": False,
                "cloud": 25,
                "Factor": 10,
                "ATR": 7,
                "sl": 2,
                "tslflag": True,
                "tp": 2,
                "ttpdist": 1,
                "tbdist": 1,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
                "fromyear": 2017,
                "toyear": 2018,
                "frommonth": 7,
                "tomonth": 6,
                "fromday": 1,
                "today": 30,
            }],
        BTStrategyEnum.S009_RSI_MIN_MAX_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "LTCUSD",
                "timeframe": "30m",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": True,
                "rsiperiod": 14,
                "rsilongopenvalue": 25,
                "rsilongclosevalue": 65,
                "rsishortopenvalue": 74,
                "rsishortclosevalue": 31,
                "sl": 2,
                "tslflag": True,
                "tp": 2,
                "ttpdist": 1,
                "tbdist": 1,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
                "fromyear": 2017,
                "toyear": 2018,
                "frommonth": 1,
                "tomonth": 6,
                "fromday": 1,
                "today": 30,
            }],
        BTStrategyEnum.S010_ALEX_AROON_TREND_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSD",
                "timeframe": "3h",
                "startcash": 1500,
                "lotsize": 1470,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": True,
                "aroon_length": 200,
                "cross_r1_start": 10,
                "cross_r1_end": 80,
                "cross_r2_start": 85,
                "cross_r2_end": 100,
                "sl": 0,
                "tslflag": False,
                "tp": 2,
                "ttpdist": 0,
                "tbdist": 0,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
                "fromyear": 2017,
                "toyear": 2019,
                "frommonth": 8,
                "tomonth": 1,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S011_EMA_CROSS_OVER_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSD",
                "timeframe": "1h",
                "startcash": 100000,
                "lotsize": 10000,
                "lottype": "Fixed"
            },  {
                "needlong": True,
                "needshort": True,
                "ema_ratio": 0.5,
                "slow_ema_period": 200,
                "sl": 2,
                "tslflag": True,
                "tp": 2,
                "ttpdist": 1,
                "tbdist": 1,
                "numdca": 2,
                "dcainterval": 3,
                "dcasltimeout": 0,
                "fromyear": 2018,
                "toyear": 2018,
                "frommonth": 6,
                "tomonth": 12,
                "fromday": 1,
                "today": 31,
            }],
        BTStrategyEnum.S012_GRID_MARKET_MAKER_STRATEGY_ID: [
            {
                "exchange": "bitfinex",
                "currency_pair": "BTCUSD",
                "timeframe": "1m",
                "startcash": 100000,
                "lotsize": 1,
                "lottype": "Fixed"
            },  {
                "order_pairs": 15,
                "order_start_size": 0.01,
                "order_step_size": 0.001,
                "interval_pct": 0.02,
                "min_spread_pct": 0.005,
                "relist_interval_pct": 0.002,
                "min_position": -1.5,
                "max_position": 1.5,
                "stop_quoting_if_inside_loss_range": True,
                "fromyear": 2019,
                "toyear": 2019,
                "frommonth": 6,
                "tomonth": 6,
                "fromday": 5,
                "today": 9,
            }]
    }

    _STEP1_STRATEGY_PARAMS_DICT = {
        BTStrategyEnum.S001_ALEX_NORO_TRENDMAS_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "usefastsma": True,
            "fastlen": range(3, 8, 2),
            "slowlen": range(10, 27, 2),
            "bars": range(0, 3),
            "needex": (False, True),
            "sl": 0,
            "tslflag": False,
            "tp": (0, 1, 2, 3),
            "ttpdist": 0,
            "tbdist": 0,
            "numdca": (0, 2, 3, 4),
            "dcainterval": (0, 0.2, 0.5),
            "dcasltimeout": (0, 2, 4)
        },
        BTStrategyEnum.S002_ALEX_NORO_SILA_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "sensup": 5,  # range(0, 9),
            "sensdn": 5,  # range(0, 9),
            "usewow": True,
            "usebma": True,
            "usebc": True,
            "usest": True,
            "usedi": True,
            "usetts": True,
            "usersi": True,
            "usewto": True,
            "uselocoentry": False,  # (False, True),
            "sl": range(0, 16),
            "tslflag": False,
            "tp": range(0, 15),
            "ttpdist": 0,
            "tbdist": 0,
            "numdca": (0, 2, 3, 4),
            "dcainterval": (0, 1, 2, 3),
            "dcasltimeout": 0
        },
        BTStrategyEnum.S003_ALEX_NORO_ROBOT_BITMEX_FAST_RSI_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
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
            "sl": (0, 1, 2),
            "tslflag": (False, True),
            "tp": (0, 1, 2),
            "ttpdist": (0, 0.5, 1),
            "tbdist": (0, 1, 2),
            "numdca": 2,
            "dcainterval": 3,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S004_ALEX_NORO_BANDS_SCALPER_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "takepercent": range(0, 5),
            "needbe": (False, True),
            "needct": (False, True),
            "bodylen": range(0, 13, 3),
            "trb": range(1, 5),
            "len": 20,
            "sl": (0, 2, 4, 6),
            "tslflag": False,
            "tp": (0, 2, 4, 6),
            "ttpdist": (0, 1),
            "tbdist": (0, 2),
            "numdca": 0,
            "dcainterval": 0,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S005_ALEX_NORO_TRIPLE_RSI_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "leverage": 1,
            "indi": (2, 3),
            "accuracy": range(1, 11),
            "isreversive": (False, True),
            "sl": (0, 1, 2),
            "tslflag": (False, True),
            "tp": (0, 1, 2),
            "ttpdist": (0, 0.5, 1),
            "tbdist": (0, 1, 2),
            "numdca": 2,
            "dcainterval": 3,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S006_ALEX_NORO_SQUEEZE_MOMENTUM_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "length": 20,
            "mult": 2.0,
            "lengthKC": 20,
            "multKC": 1.5,
            "usecolor": (False, True),
            "usebody": (False, True),
            "sl": (0, 2, 4, 6),
            "tslflag": False,
            "tp": (0, 2, 4, 6),
            "ttpdist": (0, 2),
            "tbdist": (0, 2),
            "numdca": (0, 2),
            "dcainterval": (0, 1, 2),
            "dcasltimeout": 0
        },
        BTStrategyEnum.S007_ALEX_NORO_MULTIMA_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "usema1": True,
            "usema2": True,
            "lenma1": (10, 20, 40, 80, 100, 120, 150, 180, 200),
            "lenma2": (10, 20, 40, 80, 100, 120, 150, 180, 200),
            "usecf": (False, True),
            "sl": (0, 1, 2),
            "tslflag": (False, True),
            "tp": (0, 1, 2),
            "ttpdist": (0, 0.5, 1),
            "tbdist": (0, 1, 2),
            "numdca": 2,
            "dcainterval": 3,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S008_ALEX_NORO_SUPERTREND_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "cloud": 25,
            "Factor": range(1, 11),
            "ATR": 7,
            "sl": (0, 1, 2),
            "tslflag": (False, True),
            "tp": (0, 1, 2),
            "ttpdist": (0, 0.5, 1),
            "tbdist": (0, 1, 2),
            "numdca": 2,
            "dcainterval": 3,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S009_RSI_MIN_MAX_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "rsiperiod": (7, 14),
            "rsilongopenvalue": 30,
            "rsilongclosevalue": range(50, 71, 5),
            "rsishortopenvalue": 70,
            "rsishortclosevalue": range(30, 51, 5),
            "sl": (0, 1, 2),
            "tslflag": (False, True),
            "tp": (0, 1, 2),
            "ttpdist": (0, 0.5, 1),
            "tbdist": (0, 1, 2),
            "numdca": 2,
            "dcainterval": 3,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S010_ALEX_AROON_TREND_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "aroon_length": range(50, 251, 25),
            "cross_r1_start": (10, 15, 20, 25, 30),
            "cross_r1_end": 80,
            "cross_r2_start": (80, 85, 90),
            "cross_r2_end": 100,
            "sl": (0, 1, 2),
            "tslflag": (False, True),
            "tp": (0, 1, 2),
            "ttpdist": (0, 0.5, 1),
            "tbdist": (0, 1, 2),
            "numdca": 2,
            "dcainterval": 3,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S011_EMA_CROSS_OVER_STRATEGY_ID: {
            "needlong": True,
            "needshort": True,
            "ema_ratio": (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
            "slow_ema_period": range(60, 401, 20),
            "sl": (0, 1, 2),
            "tslflag": (False, True),
            "tp": (0, 1, 2),
            "ttpdist": (0, 0.5, 1),
            "tbdist": (0, 1, 2),
            "numdca": 2,
            "dcainterval": 3,
            "dcasltimeout": 0
        },
        BTStrategyEnum.S012_GRID_MARKET_MAKER_STRATEGY_ID: {
            "order_pairs": (15, 20),
            "order_start_size": 0.01,
            "order_step_size": (0.001, 0.003, 0.005),
            "interval_pct": (0.002, 0.005, 0.01, 0.02),
            "min_spread_pct": (0.002, 0.005, 0.01, 0.02),
            "relist_interval_pct": (0.002, 0.005, 0.01, 0.02),
            "min_position": -1.5,
            "max_position": 1.5,
            "stop_quoting_if_inside_loss_range": True,
        }
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
    def is_global_equitycurve_img_x_axis_trades(cls):
        return cls._GLOBAL_STRATEGY_PARAMS_DICT["DRAW_EQUITYCURVE_IMG_X_AXIS_TRADES"]

    @classmethod
    def get_step1_strategy_params(cls, strategy_enum):
        return cls._STEP1_STRATEGY_PARAMS_DICT[strategy_enum]

    @classmethod
    def get_default_strategy_params(cls, strategy_enum):
        return cls._DEFAULT_STRATEGY_PARAMS_DICT[strategy_enum]
