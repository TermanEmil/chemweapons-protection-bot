import json
import telegram
from telegram_bot import get_bot
from handle_message import handle_message


def lambda_handler(event, context):
    update = telegram.Update.de_json(json.loads(event['body']), get_bot())
    handle_message(update)

    return {"statusCode": 204}