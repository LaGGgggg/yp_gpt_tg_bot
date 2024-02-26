# Как запустить проект?

## Добавляем переменные окружения

Создайте файл `.env`. После, скопируйте это в него и добавте ваш бот токен

```dotenv
BOT_TOKEN=<your_bot_token>
DEBUG_ID=<your_tg_id>  # не обязательно, нужно для использования команды /debug
```

## Запуск при помощи docker compose

```bash
git clone https://github.com/LaGGgggg/yp_gpt_tg_bot
cd yp_rpg_bot
docker compose up -d --build
```

## Запуск при помощи docker

```bash
git clone https://github.com/LaGGgggg/yp_gpt_tg_bot
cd yp_rpg_bot
docker build . -t tg-bot
docker run --detach -it -p 8080:8080 tg-bot
```
