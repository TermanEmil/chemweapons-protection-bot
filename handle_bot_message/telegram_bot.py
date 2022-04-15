import os

import telegram


_bot = None


def get_bot() -> telegram.Bot:
    global _bot

    if _bot is None:
        _bot = telegram.Bot(os.environ.get("TELEGRAM_BOT_TOKEN"))
    return _bot
