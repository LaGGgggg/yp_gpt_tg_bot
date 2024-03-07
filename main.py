from random import choice

from telebot import TeleBot, types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

from gpt import GPT, get_prompt_tokens_amount
from settings import (
    REQUEST_MAX_TOKENS, WARNING_LOG_FILE_PATH, ROLE_CHOICES, SUBJECT_CHOICES_VERBOSE_NAMES,
    DIFFICULT_CHOICES_VERBOSE_NAMES, SYSTEM_PROMPT_START, SUBJECT_CHOICES_VERBOSE_NAMES_TO_SUBJECTS,
    DIFFICULT_CHOICES_VERBOSE_NAMES_TO_DIFFICULTS, DIFFICULT_CHOICES_DB_VALUES_TO_DIFFICULTS,
    SUBJECT_CHOICES_DB_VALUES_TO_SUBJECTS, ROLE_CHOICES_ROLE_BY_DB_VALUE, set_up_env_var
)
from get_logger import get_logger
from database import SessionLocal, create_all_tables
from crud import UserCrud, HistoryRecordCrud
from models import HistoryRecord


class ChatStates(StatesGroup):

    not_chat = State()
    set_subject = State()
    set_difficult = State()
    chat = State()


BOT_TOKEN: str
DEBUG_ID: int


def run_bot() -> None:

    end_chat_command = 'end_chat'
    help_command = 'help'

    bot = TeleBot(BOT_TOKEN, state_storage=StateMemoryStorage())

    bot.add_custom_filter(custom_filters.StateFilter(bot))

    help_button = types.KeyboardButton(text=f'/{help_command}')

    no_chat_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    no_chat_markup.add(help_button)
    no_chat_markup.add(types.KeyboardButton(text='/new_chat'))

    chat_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    chat_markup.add(help_button)
    chat_markup.add(types.KeyboardButton(text=f'/{end_chat_command}'))

    set_subject_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    set_subject_markup.add(help_button)

    for subject_verbose_name in SUBJECT_CHOICES_VERBOSE_NAMES:
        set_subject_markup.add(types.KeyboardButton(text=subject_verbose_name))

    set_difficult_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    set_difficult_markup.add(help_button)

    for difficult_verbose_name in DIFFICULT_CHOICES_VERBOSE_NAMES:
        set_difficult_markup.add(types.KeyboardButton(text=difficult_verbose_name))

    @bot.message_handler(commands=[help_command, 'start'])
    def help_handler(message: types.Message):

        if bot.get_state(message.from_user.id, message.chat.id) is None:
            bot.set_state(message.from_user.id, ChatStates.not_chat, message.chat.id)

        reply_message = (
            'Привет, я - бот-GPT, вот мой функционал:\n'
            f'/{help_command} или /start - список всех команд (ты уже тут)\n'
            '/new_chat - создание нового чата с GPT\n'
            f'/{end_chat_command} - удаление чата, очистка истории сообщений'
        )

        if bot.get_state(message.from_user.id, message.chat.id) == ChatStates.chat.name:
            reply_markup = chat_markup

        else:
            reply_markup = no_chat_markup

        bot.reply_to(message, reply_message, parse_mode='HTML', reply_markup=reply_markup)

    @bot.message_handler(
        commands=[end_chat_command], state=[ChatStates.chat, ChatStates.set_subject, ChatStates.set_difficult]
    )
    def end_chat(message: types.Message):

        bot.set_state(message.from_user.id, ChatStates.not_chat, message.chat.id)

        with SessionLocal() as db:

            user = UserCrud(db).get(telegram_id=message.from_user.id)

            HistoryRecordCrud(db).delete_many(user=user)

        bot.reply_to(
            message,
            'История чата удалена, спасибо за использование бота! Вы можете начать новый чат: /new_chat',
            reply_markup=no_chat_markup,
        )

    @bot.message_handler(state=ChatStates.chat)
    def process_chat_message(message: types.Message):

        message_text = message.text

        # Safety checks (a user must be able to exit a chat and view a list of bot commands):
        if message_text == f'/{end_chat_command}':

            end_chat(message)

            return

        elif message_text == f'/{help_command}':

            help_handler(message)

            return

        if get_prompt_tokens_amount(message_text) > REQUEST_MAX_TOKENS:

            bot.reply_to(message, 'Сообщение слишком длинное, пожалуйста, укоротите его', reply_markup=chat_markup)

            return

        with SessionLocal() as db:

            user = UserCrud(db).get(telegram_id=message.from_user.id)

            messages_history_db: list[HistoryRecord] = HistoryRecordCrud(db).get_many(user=user)

            messages_history = []

            for message_history in messages_history_db:
                messages_history.append(
                    {'role': ROLE_CHOICES_ROLE_BY_DB_VALUE[message_history.role], 'content': message_history.message}
                )

            system_prompt = (
                    SYSTEM_PROMPT_START + SUBJECT_CHOICES_DB_VALUES_TO_SUBJECTS[user.subject]['gpt_prompt'] +
                    DIFFICULT_CHOICES_DB_VALUES_TO_DIFFICULTS[user.difficult]['gpt_prompt']
            )

            gpt_answer = GPT(messages_history, system_prompt).ask(message_text)

            HistoryRecordCrud(db).create(user=user, message=message_text, role=ROLE_CHOICES['user'])
            HistoryRecordCrud(db).create(user=user, message=gpt_answer, role=ROLE_CHOICES['assistant'])

        bot.reply_to(message, gpt_answer, reply_markup=chat_markup)

    @bot.message_handler(commands=['new_chat'], state=ChatStates.not_chat)
    def new_chat(message: types.Message):

        bot.set_state(message.from_user.id, ChatStates.set_subject, message.chat.id)

        bot.reply_to(message, 'Выбери предмет', reply_markup=set_subject_markup)

    @bot.message_handler(state=ChatStates.set_subject)
    def process_set_subject(message: types.Message):

        if message.text not in SUBJECT_CHOICES_VERBOSE_NAMES:

            bot.reply_to(
                message,
                'Это не является корректным значением, пожалуйста, выберите ещё раз',
                reply_markup=set_subject_markup,
            )

            return

        user_id = message.from_user.id

        with SessionLocal() as db:

            user_crud = UserCrud(db)

            subject_db_value = SUBJECT_CHOICES_VERBOSE_NAMES_TO_SUBJECTS[message.text]['db_value']

            if user := user_crud.get(telegram_id=user_id):
                user_crud.update(user, subject=subject_db_value)

            else:
                user_crud.create(telegram_id=user_id, subject=subject_db_value)

        bot.set_state(user_id, ChatStates.set_difficult, message.chat.id)

        bot.reply_to(message, 'Выбери сложность объяснения', reply_markup=set_difficult_markup)

    @bot.message_handler(state=ChatStates.set_difficult)
    def process_set_difficult(message: types.Message):

        if message.text not in DIFFICULT_CHOICES_VERBOSE_NAMES:

            bot.reply_to(
                message,
                'Это не является корректным значением, пожалуйста, выберите ещё раз',
                reply_markup=set_difficult_markup,
            )

            return

        user_id = message.from_user.id

        with SessionLocal() as db:

            user_crud = UserCrud(db)

            difficult_db_value = DIFFICULT_CHOICES_VERBOSE_NAMES_TO_DIFFICULTS[message.text]['db_value']

            if user := user_crud.get(telegram_id=user_id):
                user_crud.update(user, difficult=difficult_db_value)

            else:
                user_crud.create(telegram_id=user_id, difficult=difficult_db_value)

        bot.set_state(user_id, ChatStates.chat, message.chat.id)

        bot.reply_to(message, 'Задайте свой вопрос GPT:', reply_markup=chat_markup)

    @bot.message_handler(commands=['debug'], func=lambda message: message.from_user.id == DEBUG_ID)
    def debug_handler(message: types.Message):
        with open(WARNING_LOG_FILE_PATH, 'rb') as f:

            file_data = f.read()

            if not file_data:

                bot.reply_to(message, 'Файл с логами ошибок пуст!')

                return

            bot.send_document(message.chat.id, file_data, visible_file_name='logs.log')

    @bot.message_handler(content_types=['text'])
    def unknown_text_handler(message: types.Message):

        replies = (
            'О, круто!',
            'Верно подмечено!',
            'Как с языка снял',
            'Какой ты всё-таки умный',
            'По-любому что-то умное написал',
            'Как лаконично-то!',
        )

        if bot.get_state(message.from_user.id, message.chat.id) == ChatStates.chat.name:
            reply_markup = chat_markup

        else:
            reply_markup = no_chat_markup

        help_message = (
            '\n\nЕсли ты хотел, чтобы я что-то сделал, то я не распознал твою команду, пожалуйста,'
            f' сверься с /{help_command}'
        )

        bot.reply_to(message, choice(replies) + help_message, reply_markup=reply_markup)

    bot.infinity_polling()


def main():

    global BOT_TOKEN, DEBUG_ID

    logger = get_logger('main')

    DEBUG_ID = set_up_env_var('DEBUG_ID', logger.warning)

    if BOT_TOKEN := set_up_env_var('BOT_TOKEN', logger.error):

        create_all_tables()

        run_bot()

    else:
        logger.error('Setup cannot be completed, some errors occurred')


if __name__ == '__main__':
    main()
