import sys

import telegram
from telegram.error import Unauthorized, BadRequest

from Lecture import LecturesRepository
from BotSession import BotSessionsRepository
from aws import get_db, get_db_client
from form_handling import resolve_form_step, RequestToStart
from telegram_bot import get_bot


def handle_message(update: telegram.Update):
    if update is None or update.message is None:
        return

    if update.message.from_user is None or update.message.from_user.is_bot:
        return

    try:
        handle_core(update)
    except Unauthorized as e:
        print(f"Unauthorized: {e}", file=sys.stderr)
    except BadRequest as e:
        print(f"Bad request: {e}", file=sys.stderr)


def handle_core(update: telegram.Update):
    sessions_repo = BotSessionsRepository(get_db())
    lectures_repo = LecturesRepository(get_db(), get_db_client())

    session = sessions_repo.get_session(update.message.chat_id)

    if update.message.text == '/start':
        session.form_step = RequestToStart.__name__

    form_step = resolve_form_step(session.form_step, get_bot(), sessions_repo, lectures_repo)
    next_step_name = form_step.handle(update)

    next_step = resolve_form_step(next_step_name, get_bot(), sessions_repo, lectures_repo)
    next_step.request(update)

    session = sessions_repo.get_session(update.message.chat_id)
    session.form_step = type(next_step).__name__
    sessions_repo.update_session(session)
