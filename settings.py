from pathlib import Path


LOGS_DIR = Path(__file__).resolve().parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

WARNING_LOG_FILE_PATH = LOGS_DIR / 'warning.log'

SYSTEM_PROMPT = (
    'You MUST answer polite and friendly, you are a helping person, you must create a good mood for him, cheer him up'
    ' and please him'
)
GPT_URL = 'http://localhost:1234/v1/chat/completions'
GPT_MODEL = 'mistralai/mistral-7b-instruct-v0.2'
RESPONSE_MAX_TOKENS = 250
GPT_TEMPERATURE = 1

REQUEST_MAX_TOKENS = 500
