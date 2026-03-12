# Handoff — Memorial MVP
> Обновлено: 2026-03-12

## Что сейчас делается
Реализован Telegram-бот для чата с AI-аватаром через RAG-пайплайн.

## Последнее действие
Создан модуль `backend/bot/` (5 файлов): main.py, handlers.py, session.py, keyboards.py, api_client.py.
Обновлены config.py (3 новых поля), requirements.txt (python-telegram-bot==20.7), .env.example.

## Следующий шаг
1. Добавить `TELEGRAM_BOT_TOKEN=...` в `backend/.env`
2. Установить зависимость: `pip install python-telegram-bot==20.7`
3. Запустить бота: `cd backend && source .venv/bin/activate && python -m bot.main`
4. Для аудио в dev: запустить ngrok → `PUBLIC_API_URL=https://xxxx.ngrok.io` в .env

## Незавершённые задачи
- Deep link кнопка на фронте (в SharePanel) — опционально
- Webhook-режим для production (сейчас только long polling)

## Изменённые файлы (текущая сессия)
- `backend/app/config.py` — +TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME, BOT_API_BASE_URL
- `backend/requirements.txt` — +python-telegram-bot==20.7
- `backend/.env.example` — добавлены Telegram-переменные
- `backend/bot/__init__.py` — создан
- `backend/bot/main.py` — точка входа, polling loop
- `backend/bot/handlers.py` — хэндлеры /start /change /voice /family /help + текст
- `backend/bot/session.py` — Redis/in-memory сессия пользователя
- `backend/bot/keyboards.py` — inline keyboards (мемориалы, настройки)
- `backend/bot/api_client.py` — HTTP-клиент к FastAPI

## Запуск стека
```bash
# Терминал 1: Backend API
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Терминал 2: Telegram Bot
cd backend && source .venv/bin/activate && python -m bot.main

# Фронтенд
cd frontend && npm run dev

# Опционально: ngrok для публичных аудио-URL
ngrok http 8000
```

## Критический контекст
- audio_url из API приходит как `/api/v1/media/audio/file.mp3` (относительный)
- build_audio_url() в api_client.py делает его абсолютным через PUBLIC_API_URL или BOT_API_BASE_URL
- Telegram скачивает аудио по URL сам — нужен публичный URL (ngrok в dev)
- Сессия хранится в Redis (ключ `tg:{chat_id}`), fallback — in-memory dict
- owner_id=1 хардкод в API, аутентификации нет — все мемориалы доступны боту
