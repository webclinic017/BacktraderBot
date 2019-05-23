#!/usr/bin/env python3

from bot.config.bot_strategy_config import BotStrategyConfig
from bot.config.bot_config import BotConfig
import requests

def get_telegram_message_text(bot_id, txt):
    return "<b>{}</b>: {}".format(bot_id, txt)

def send_telegram_message(message=""):
    base_url = "https://api.telegram.org/bot{}".format(BotConfig.get_telegram_config().get("bot"))
    bot_id = BotStrategyConfig.get_instance().botid.upper()
    telegram_txt = get_telegram_message_text(bot_id, message)
    #print("Sending message to Telegram: {}".format(message))
    return requests.get("{}/sendMessage".format(base_url), params={
        'chat_id': BotConfig.get_telegram_config().get("channel"),
        'text': telegram_txt,
        'parse_mode': 'html'  # or html
    })

