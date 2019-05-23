#!/usr/bin/env python3
import configparser
import os

SECTION_NAME = 'Config'


class BotStrategyConfig(object):
    _instance = None

    def __init__(self, botid, start_cash, strategy, exchange, target_currency, reference_currency, timeframe, strategy_params_json, order_size):
        self.botid = botid
        self.start_cash = start_cash
        self.strategy = strategy
        self.exchange = exchange
        self.target_currency = target_currency
        self.reference_currency = reference_currency
        self.timeframe = timeframe
        self.strategy_params_json = strategy_params_json
        self.order_size = order_size

    @classmethod
    def whereAmI(cls):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    @classmethod
    def get_bot_config_file_path(cls):
        return "{}/{}".format(cls.whereAmI(), "config/bot_strategy_config.ini")

    @classmethod
    def get_prop_name(cls, botid, prop):
        return "{}.{}".format(botid, prop)

    @classmethod
    def parse_bot_strategies_config(cls, botid):
        config = configparser.ConfigParser()
        config.read_file(open(cls.get_bot_config_file_path()))
        return BotStrategyConfig(botid=botid,
                                 start_cash=config[SECTION_NAME][cls.get_prop_name(botid, "start_cash")],
                                 strategy=config[SECTION_NAME][cls.get_prop_name(botid, "strategy")],
                                 exchange=config[SECTION_NAME][cls.get_prop_name(botid, "exchange")],
                                 target_currency=config[SECTION_NAME][cls.get_prop_name(botid, "target_currency")],
                                 reference_currency=config[SECTION_NAME][cls.get_prop_name(botid, "reference_currency")],
                                 timeframe=int(config[SECTION_NAME][cls.get_prop_name(botid, "timeframe")]),
                                 strategy_params_json=config[SECTION_NAME][cls.get_prop_name(botid, "strategy_params")],
                                 order_size=float(config[SECTION_NAME][cls.get_prop_name(botid, "order_size")]))

    @classmethod
    def create_instance(cls, botid):
        if cls._instance is None:
            cls._instance = cls.parse_bot_strategies_config(botid)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls._instance
