from pathlib import Path
from os import environ
from typing import Callable

from dotenv import load_dotenv


LOGS_DIR = Path(__file__).resolve().parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

WARNING_LOG_FILE_PATH = LOGS_DIR / 'warning.log'

SYSTEM_PROMPT_START = 'You MUST answer polite and friendly, you are a helping person. '
SYSTEM_PROMPT_TEMPLATE_SUBJECT = 'You MUST help with {subject} subject.'
GPT_URL = 'http://localhost:1234/v1/chat/completions'
GPT_MODEL = 'mistralai/mistral-7b-instruct-v0.2'
RESPONSE_MAX_TOKENS = 250
GPT_TEMPERATURE = 1

REQUEST_MAX_TOKENS = 500

SUBJECT_CHOICES: dict[str, dict[str, int | str]] = {
    'math': {
        'db_value': 0,
        'gpt_prompt': SYSTEM_PROMPT_TEMPLATE_SUBJECT.format(subject='math'),
        'verbose_name': 'математика',
    },
    'english': {
        'db_value': 1,
        'gpt_prompt': SYSTEM_PROMPT_TEMPLATE_SUBJECT.format(subject='english'),
        'verbose_name': 'английский',
    },
    'chemistry': {
        'db_value': 2,
        'gpt_prompt': SYSTEM_PROMPT_TEMPLATE_SUBJECT.format(subject='chemistry'),
        'verbose_name': 'химия',
    },
}
SUBJECT_CHOICES_VERBOSE_NAMES: list[str] = [subject['verbose_name'] for subject in SUBJECT_CHOICES.values()]
SUBJECT_CHOICES_VERBOSE_NAMES_TO_SUBJECTS: dict = \
    {subject['verbose_name']: subject for subject in SUBJECT_CHOICES.values()}
SUBJECT_CHOICES_DB_VALUES_TO_SUBJECTS: dict = \
    {subject['db_value']: subject for subject in SUBJECT_CHOICES.values()}

DIFFICULT_CHOICES: dict[str, dict[str, int | str]] = {
    'easy': {
        'db_value': 0,
        'gpt_prompt': 'You MUST answer in accordance with the level of the novice user, explain everything simply.',
        'verbose_name': 'простая',
    },
    'hard': {
        'db_value': 1,
        'gpt_prompt': 'You MUST answer at a professional user level, advanced terms may be used.',
        'verbose_name': 'хард',
    },
}
DIFFICULT_CHOICES_VERBOSE_NAMES: list[str] = [difficult['verbose_name'] for difficult in DIFFICULT_CHOICES.values()]
DIFFICULT_CHOICES_VERBOSE_NAMES_TO_DIFFICULTS: dict = \
    {difficult['verbose_name']: difficult for difficult in DIFFICULT_CHOICES.values()}
DIFFICULT_CHOICES_DB_VALUES_TO_DIFFICULTS: dict = \
    {difficult['db_value']: difficult for difficult in DIFFICULT_CHOICES.values()}

ROLE_CHOICES: dict[str, int] = {
    'system': 0,
    'user': 1,
    'assistant': 2,
}
ROLE_CHOICES_ROLE_BY_DB_VALUE = {value: key for key, value in ROLE_CHOICES.items()}


def set_up_env_var(env_var_name: str, error_log_function: Callable) -> str | None:

    load_dotenv()

    result = environ.get(env_var_name)

    if not result:

        error_log_function(f'{env_var_name} environment variable is not set!')

        return None

    return result
