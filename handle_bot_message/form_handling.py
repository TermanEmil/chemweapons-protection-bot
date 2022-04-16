from abc import ABC

import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton

from Lecture import LecturesRepository
from BotSession import BotSessionsRepository
from spreadsheets import add_to_spreadsheet


class FormStep(ABC):
    def request(self, update: telegram.Update):
        pass

    def handle(self, update: telegram.Update) -> str:
        raise


class RequestToStart(FormStep):
    def __init__(self, bot: telegram.Bot):
        self.bot = bot

    def request(self, update: telegram.Update):
        markup = ReplyKeyboardMarkup([["/start"]], one_time_keyboard=True, resize_keyboard=True)
        self.bot.send_message(update.message.chat_id, "Натисніть /start щоб почати", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        if update.message.text not in ["/start"]:
            return self.__class__.__name__

        return ChooseBetweenLessonOrQuestion.__name__


class ChooseBetweenLessonOrQuestion(FormStep):
    def __init__(self, bot: telegram.Bot):
        self.bot = bot

    def request(self, update: telegram.Update):
        markup = ReplyKeyboardMarkup(
            [["Отримати матерiали щодо лекції", "Задати питання щодо лекції"]],
            one_time_keyboard=True,
            resize_keyboard=True)
        self.bot.send_message(update.message.chat_id, "Виберіть із наступного", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        if update.message.text not in ["Отримати матерiали щодо лекції", "Задати питання щодо лекції"]:
            return self.__class__.__name__

        if update.message.text == "Отримати матерiали щодо лекції":
            return ChooseLectureToLearnAbout.__name__
        elif update.message.text == "Задати питання щодо лекції":
            return ChooseLectureToAskAQuestionAbout.__name__
        else:
            return self.__class__.__name__


class ChooseLectureToLearnAbout(FormStep):
    def __init__(self, bot: telegram.Bot, lectures_repo: LecturesRepository):
        self.bot = bot
        self.lectures_repo = lectures_repo

    def request(self, update: telegram.Update):
        lectures_names = [[x.name] for x in self.lectures_repo.find_all_lectures()]
        markup = ReplyKeyboardMarkup(lectures_names, one_time_keyboard=True, resize_keyboard=True)
        self.bot.send_message(update.message.chat_id, "Виберіть лекцію", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        lectures = self.lectures_repo.find_all_lectures()
        possible_lectures = [lecture for lecture in lectures if lecture.name == update.message.text]

        if len(possible_lectures) == 0:
            self.bot.send_message(update.message.chat_id, "Лекції не знайдено")
            return self.__class__.__name__

        lecture = possible_lectures[0]

        if lecture.url is None or len(lecture.url) == 0:
            self.bot.send_message(
                update.message.chat_id,
                "Дана лекцiя ще не вiдбулась, всі матеріали щодо даної лекції можна буде отримати згодом.")

            return RequestToStart.__name__

        self.bot.send_message(update.message.chat_id, lecture.url)
        return RequestToStart.__name__


class ChooseLectureToAskAQuestionAbout(FormStep):
    def __init__(self, bot: telegram.Bot, sessions_repo: BotSessionsRepository, lectures_repo: LecturesRepository):
        self.bot = bot
        self.sessions_repo = sessions_repo
        self.lectures_repo = lectures_repo

    def request(self, update: telegram.Update):
        lectures_names = [[x.name] for x in self.lectures_repo.find_all_lectures()]
        markup = ReplyKeyboardMarkup(lectures_names, one_time_keyboard=True, resize_keyboard=True)
        self.bot.send_message(update.message.chat_id, "Виберіть лекцію", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        lectures = self.lectures_repo.find_all_lectures()
        possible_lectures = [lecture for lecture in lectures if lecture.name == update.message.text]

        if len(possible_lectures) == 0:
            self.bot.send_message(update.message.chat_id, "Лекції не знайдено")
            return self.__class__.__name__

        lecture = possible_lectures[0]
        session = self.sessions_repo.get_session(update.message.chat_id)

        session.lecture_id_for_question = lecture.id
        self.sessions_repo.update_session(session)

        return RequestUserName.__name__


class RequestUserName(FormStep):
    def __init__(self, bot: telegram.Bot, sessions_repo: BotSessionsRepository):
        self.bot = bot
        self.sessions_repo = sessions_repo

    def request(self, update: telegram.Update):
        session = self.sessions_repo.get_session(update.message.chat_id)
        if session.user_name is None:
            options = [[]]
        else:
            options = [[session.user_name]]

        markup = ReplyKeyboardMarkup(options, one_time_keyboard=True, resize_keyboard=True)
        self.bot.send_message(update.message.chat_id, "Ваше iм’я", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        if update.message.text is None:
            return self.__class__.__name__

        session = self.sessions_repo.get_session(update.message.chat_id)
        if session.user_name != update.message.text:
            session.user_name = update.message.text
            self.sessions_repo.update_session(session)

        return RequestContactMeans.__name__


class RequestContactMeans(FormStep):
    def __init__(self, bot: telegram.Bot, sessions_repo: BotSessionsRepository):
        self.bot = bot
        self.sessions_repo = sessions_repo

    def request(self, update: telegram.Update):
        session = self.sessions_repo.get_session(update.message.chat_id)

        if session.contact_means == "Тощо":
            options = [[]]
        else:
            options = [["Телефон", "Телеграм", "Фейсбук", "Тощо"]]

        markup = ReplyKeyboardMarkup(options, one_time_keyboard=True, resize_keyboard=True)
        self.bot.send_message(update.message.chat_id, "Введіть засоби зв'язку", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        if update.message.text is None:
            return self.__class__.__name__

        session = self.sessions_repo.get_session(update.message.chat_id)

        if session.contact_means != update.message.text:
            session.contact_means = update.message.text
            session.contact = None
            self.sessions_repo.update_session(session)

        if update.message.text == "Тощо":
            return self.__class__.__name__

        return RequestContact.__name__


class RequestContact(FormStep):
    def __init__(self, bot: telegram.Bot, sessions_repo: BotSessionsRepository):
        self.bot = bot
        self.sessions_repo = sessions_repo

    def request(self, update: telegram.Update):
        session = self.sessions_repo.get_session(update.message.chat_id)

        if session.contact_means == "Телеграм":
            contact_button = KeyboardButton(text="Поділіться моїм контактом", request_contact=True)
            markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
            self.bot.send_message(update.message.chat_id, 'Поділіться моїм контактом', reply_markup=markup)
        else:
            if session.contact is None:
                options = [[]]
            else:
                options = [[session.contact]]

            markup = ReplyKeyboardMarkup(options, one_time_keyboard=True, resize_keyboard=True)
            self.bot.send_message(update.message.chat_id, "Вашi контактнi данi", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        if update.message.contact:
            contact = f"https://t.me/{update.message.contact.first_name}\n{update.message.contact.phone_number}"
        elif update.message.text:
            contact = update.message.text
        else:
            return self.__class__.__name__

        session = self.sessions_repo.get_session(update.message.chat_id)
        if session.contact != contact:
            session.contact = contact
            self.sessions_repo.update_session(session)

        return RequestQuestion.__name__


class RequestQuestion(FormStep):
    def __init__(self, bot: telegram.Bot, sessions_repo: BotSessionsRepository):
        self.bot = bot
        self.sessions_repo = sessions_repo

    def request(self, update: telegram.Update):
        self.bot.send_message(update.message.chat_id, "Ваше питання", reply_markup=None)

    def handle(self, update: telegram.Update) -> str:
        if not update.message.text:
            return self.__class__.__name__

        session = self.sessions_repo.get_session(update.message.chat_id)
        session.question = update.message.text
        self.sessions_repo.update_session(session)
        return RequestSubmission.__name__


class RequestSubmission(FormStep):
    def __init__(self, bot: telegram.Bot, sessions_repo: BotSessionsRepository, lectures_repo: LecturesRepository):
        self.bot = bot
        self.sessions_repo = sessions_repo
        self.lectures_repo = lectures_repo

    def request(self, update: telegram.Update):
        markup = ReplyKeyboardMarkup([['Отправить', 'Отмена']], one_time_keyboard=True, resize_keyboard=True)
        self.bot.send_message(update.message.chat_id, "Отправить?", reply_markup=markup)

    def handle(self, update: telegram.Update) -> str:
        if update.message.text != "Отправить":
            self.bot.send_message(update.message.chat_id, "Отменено", reply_markup=None)
            return RequestToStart.__name__

        session = self.sessions_repo.get_session(update.message.chat_id)
        lecture = self.lectures_repo.find_lecture(session.lecture_id_for_question)
        add_to_spreadsheet(session, lecture)

        self.bot.send_message(update.message.chat_id, "Надіслано")
        return RequestToStart.__name__


def resolve_form_step(
        form_step_name: str,
        bot: telegram.Bot,
        sessions_repo: BotSessionsRepository,
        lectures_repo: LecturesRepository) -> FormStep:
    if form_step_name == RequestToStart.__name__:
        return RequestToStart(bot)

    if form_step_name == ChooseBetweenLessonOrQuestion.__name__:
        return ChooseBetweenLessonOrQuestion(bot)

    if form_step_name == ChooseLectureToLearnAbout.__name__:
        return ChooseLectureToLearnAbout(bot, lectures_repo)

    if form_step_name == ChooseLectureToAskAQuestionAbout.__name__:
        return ChooseLectureToAskAQuestionAbout(bot, sessions_repo, lectures_repo)

    if form_step_name == RequestUserName.__name__:
        return RequestUserName(bot, sessions_repo)

    if form_step_name == RequestContactMeans.__name__:
        return RequestContactMeans(bot, sessions_repo)

    if form_step_name == RequestContact.__name__:
        return RequestContact(bot, sessions_repo)

    if form_step_name == RequestQuestion.__name__:
        return RequestQuestion(bot, sessions_repo)

    if form_step_name == RequestSubmission.__name__:
        return RequestSubmission(bot, sessions_repo, lectures_repo)

    raise Exception(f"{form_step_name}: unrecognized form step")
