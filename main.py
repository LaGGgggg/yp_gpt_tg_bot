from os import environ
from dotenv import load_dotenv
from random import choice
from logging import Logger

from telebot import TeleBot, types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

from user_info import UserInfoManager
from gpt import GPT, get_prompt_tokens_amount
from settings import REQUEST_MAX_TOKENS, WARNING_LOG_FILE_PATH
from get_logger import get_logger


BOT_TOKEN: str
DEBUG_ID: int


class ChatStates(StatesGroup):

    chat = State()
    not_chat = State()


def set_up(logger: Logger) -> bool:

    global BOT_TOKEN, DEBUG_ID

    # Environment variables:

    load_dotenv()

    BOT_TOKEN = environ.get('BOT_TOKEN', default=None)

    if not BOT_TOKEN:

        logger.error('BOT_TOKEN environment variable is not set!')

        return False

    DEBUG_ID = environ.get('DEBUG_ID', default=None)

    if not DEBUG_ID:

        logger.warning('DEBUG_ID environment variable is not set, you cannot use /debug')

        DEBUG_ID = 0

    else:
        DEBUG_ID = int(DEBUG_ID)

    return True


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

    @bot.message_handler(commands=[end_chat_command], state=ChatStates.chat)
    def end_chat(message: types.Message):

        bot.set_state(message.from_user.id, ChatStates.not_chat, message.chat.id)

        with UserInfoManager(message.from_user.id) as user_info_manager:
            user_info_manager.update_user_data([])

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

        with UserInfoManager(message.from_user.id) as user_info_manager:

            gpt = GPT(user_info_manager.get_user_data())

            gpt_answer = gpt.ask(message_text)

            user_info_manager.update_user_data(gpt.previous_messages)

        bot.reply_to(message, gpt_answer, reply_markup=chat_markup)

    @bot.message_handler(commands=['new_chat'], state=ChatStates.not_chat)
    def new_chat(message: types.Message):

        bot.set_state(message.from_user.id, ChatStates.chat, message.chat.id)

        bot.reply_to(message, 'Напиши своё сообщение для GPT', reply_markup=chat_markup)

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

    logger = get_logger('main')

    if set_up(logger):
        run_bot()

    else:
        logger.error('Setup cannot be completed, some errors occurred')


if __name__ == '__main__':
    main()
