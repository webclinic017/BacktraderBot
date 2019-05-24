#!/usr/bin/env python3

import time
import backtrader as bt
import datetime as dt
from bot.ccxtbt import CCXTStore
import argparse
from bot.config.bot_config import BotConfig
from bot.config.bot_strategy_config import BotStrategyConfig
from bot.config.broker_mappings import BrokerMappings
from bot.utils import send_telegram_message
from config.strategy_enum import BTStrategyEnum
from config.strategy_config import AppConfig
import atexit
import signal
import sys
import os
import ast


class BacktraderBot(object):

    def __init__(self):
        self.botid = None
        self._strategy_enum = None
        self._strategy_params = None
        self.bot_strategy_config = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Backtrader Bot')

        parser.add_argument('-b', '--botid',
                            type=str,
                            required=True,
                            help='Bot ID')

        parser.add_argument('-n', '--number_of_bots',
                            type=int,
                            required=True,
                            help='Number of bots')

        parser.add_argument('--commtype',
                            default="Percentage",
                            type=str,
                            choices=["Percentage", "Fixed"],
                            help='The type of commission to apply to a trade')

        parser.add_argument('--commission',
                            default=0.0015,
                            type=float,
                            help='The amount of commission to apply to a trade')

        parser.add_argument('--debug',
                            action='store_true',
                            default=True,
                            help=('Print Debug logs'))

        return parser.parse_args()

    def restart(self):
        print("Restarting bot...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def run_exit(self):
        try:
            print("Shutting down..")
            #self.exchange.cancel_all_orders()
            #self.exchange.bitmex.exit()
        except Exception as e:
            print("Unable to correctly shutting down the bot: {}".format(e))
        sys.exit()

    def get_rate_limit(self, number_of_bots):
        if number_of_bots == 1:
            return 4000
        else:
            return 4000 * number_of_bots / 2

    def get_broker_config(self, exchange, botid, number_of_bots):
        exchange_rest_api_config = BotConfig.get_exchange_rest_api_config_for_bot(exchange, botid)
        rate_limit = self.get_rate_limit(number_of_bots)
        return {
            'apiKey': exchange_rest_api_config.get("apikey"),
            'secret': exchange_rest_api_config.get("secret"),
            'nonce': lambda: str(int(time.time() * 1000)),
            'rateLimit': rate_limit,
            'enableRateLimit': True,
        }

    def calc_history_start_date(self, timeframe):
        prefetch_num_minutes = 500 * timeframe
        return dt.datetime.utcnow() - dt.timedelta(minutes=prefetch_num_minutes)

    def init_bot_strategy_config(self, botid):
        self.botid = botid
        self.bot_strategy_config = BotStrategyConfig.create_instance(self.botid)

    def init_cerebro(self, cerebro, args):
        exchange = self.bot_strategy_config.exchange
        broker_config = self.get_broker_config(exchange, self.bot_strategy_config.botid, args.number_of_bots)

        store = CCXTStore(exchange=exchange, currency=self.bot_strategy_config.reference_currency, config=broker_config, retries=5, debug=args.debug)

        broker_mapping = BrokerMappings.get_broker_mapping(exchange)
        broker = store.getbroker(broker_mapping=broker_mapping)
        if args.commtype.lower() == 'percentage':
            broker.setcommission(args.commission)
        cerebro.setbroker(broker)

        hist_start_date = self.calc_history_start_date(self.bot_strategy_config.timeframe)
        data = store.getdata(
            dataname='{}/{}'.format(self.bot_strategy_config.target_currency, self.bot_strategy_config.reference_currency),
            name='{}{}'.format(self.bot_strategy_config.target_currency, self.bot_strategy_config.reference_currency),
            timeframe=bt.TimeFrame.Minutes,
            fromdate=hist_start_date,
            compression=self.bot_strategy_config.timeframe,
            ohlcv_limit=500,
            drop_newest=True,
            debug=True
        )
        # Add the feed
        cerebro.adddata(data)

    def get_strategy_enum(self, strategy):
        return BTStrategyEnum.get_strategy_enum_by_str(strategy)

    def get_parameters_map(self, parameters_json):
        return ast.literal_eval(parameters_json)

    def get_bot_strategy_params(self):
        params_json = self.bot_strategy_config.strategy_params_json
        return self.get_parameters_map(params_json)

    def init_strategy_params(self, strategy_enum, args):
        default_strategy_config = AppConfig.get_default_strategy_params(strategy_enum)
        default_params_dict = default_strategy_config[1]
        bot_strategy_params_dict = self.get_bot_strategy_params()
        self._strategy_params = default_params_dict.copy()
        self._strategy_params.update(bot_strategy_params_dict)
        self._strategy_params.update(
            {
                ("debug", args.debug),
            }
        )

    def add_strategy(self, cerebro):
        strategy_class = self._strategy_enum.value.clazz
        cerebro.addstrategy(strategy_class, **self._strategy_params)

    def run(self):
        atexit.register(exit)
        signal.signal(signal.SIGTERM, exit)

        args = self.parse_args()
        self.init_bot_strategy_config(args.botid)

        strategy = BotStrategyConfig.get_instance().strategy
        self._strategy_enum = self.get_strategy_enum(strategy)
        self.init_strategy_params(self._strategy_enum, args)

        cerebro = bt.Cerebro(quicknotify=True)
        self.init_cerebro(cerebro, args)
        self.add_strategy(cerebro)

        cerebro.run()


def main():
    bot = BacktraderBot()
    bot.run()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Running finished.")
        time = dt.datetime.now().strftime("%d-%m-%y %H:%M")
        send_telegram_message("Bot finished by user at {}".format(time))
    except Exception as err:
        send_telegram_message("Bot finished with error: {}".format(err))
        print("Finished with error: {}".format(err))
        raise
