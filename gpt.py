from requests import Session
from transformers import AutoTokenizer

from get_logger import get_logger
from settings import GPT_URL, GPT_MODEL, RESPONSE_MAX_TOKENS, GPT_TEMPERATURE


tokenizer = AutoTokenizer.from_pretrained(GPT_MODEL)


def get_prompt_tokens_amount(prompt: str) -> int:
    return len(tokenizer.encode(prompt))


class GPT:

    def __init__(self, previous_messages: list[dict[str, str]], system_prompt: str) -> None:

        self.previous_messages = previous_messages
        self.system_prompt = system_prompt
        self.logger = get_logger('main')

        with Session() as session:
            self.session = session

    def ask(self, prompt: str) -> str:

        error_message = 'Произошла ошибка, пожалуйста, повторите попытку или обратитесь в поддержку'

        user_message = {'role': 'user', 'content': prompt}

        try:
            response = self.session.post(
                GPT_URL,
                headers={'Content-Type': 'application/json'},
                json={
                    'messages': [
                        {'role': 'system', 'content': self.system_prompt},
                        *self.previous_messages,
                        user_message,
                    ],
                    'temperature': GPT_TEMPERATURE,
                    'max_tokens': RESPONSE_MAX_TOKENS,
                    'stream': False,
                },
            )

        except Exception as e:

            self.logger.error(f'An exception occurred while requesting gpt answer ({prompt=}): {e}')

            return error_message

        response_status_code = response.status_code

        if response_status_code != 200:

            self.logger.error(f'Incorrect gpt answer status code: {response_status_code} ({prompt=})')

            return error_message

        answer = response.json()['choices'][0]['message']['content']

        self.previous_messages.append(user_message)
        self.previous_messages.append({'role': 'assistant', 'content': answer})

        return answer
