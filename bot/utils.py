import requests

from bot.config import TELEGRAM, ENV

def send_telegram_message(message=""):
    base_url = "https://api.telegram.org/bot{}".format(TELEGRAM.get("bot"))
    #print("Sending message to Telegram: {}".format(message))
    return requests.get("{}/sendMessage".format(base_url), params={
        'chat_id': TELEGRAM.get("channel"),
        'text': message
    })
