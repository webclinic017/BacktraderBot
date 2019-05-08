#!/usr/bin/env python3
import configparser

class BotStrategyConfig(object):
    def __init__(self, botid, strategy, exchange, target_currency, reference_currency, timeframe, strategy_params_json):
        self.botid = botid
        self.strategy = strategy
        self.exchange = exchange
        self.target_currency = target_currency
        self.reference_currency = reference_currency
        self.timeframe = timeframe
        self.strategy_params_json = strategy_params_json


class BotConfigParser(object):
    @classmethod
    def get_prop_name(cls, botid, prop):
        return "{}.{}".format(botid, prop)

    @classmethod
    def parse_bot_strategies_config(cls, botid):
        config = configparser.ConfigParser()
        config.read('./bot/config/bot_strategies_config.ini')
        return BotStrategyConfig(botid=botid,
                                 strategy=BotConfigParser.get_prop_name(botid, "strategy"),
                                 exchange=BotConfigParser.get_prop_name(botid, "exchange"),
                                 target_currency=BotConfigParser.get_prop_name(botid, "target_currency"),
                                 reference_currency=BotConfigParser.get_prop_name(botid, "reference_currency"),
                                 timeframe=BotConfigParser.get_prop_name(botid, "timeframe"),
                                 strategy_params_json=BotConfigParser.get_prop_name(botid, "strategy_params"))

