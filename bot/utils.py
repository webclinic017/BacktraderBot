import requests
import os

from bot.config.bot_config import BotConfig


def send_telegram_message(message=""):
    base_url = "https://api.telegram.org/bot{}".format(BotConfig.get_telegram_config().get("bot"))
    #print("Sending message to Telegram: {}".format(message))
    return requests.get("{}/sendMessage".format(base_url), params={
        'chat_id': BotConfig.get_telegram_config().get("channel"),
        'text': message
    })


def whereAmI():
    return os.path.dirname(os.path.realpath(__import__("__main__").__file__))
