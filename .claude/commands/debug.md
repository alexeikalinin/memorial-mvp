Диагностируй проблему в проекте memorial-mvp и дай конкретное решение.

Аргумент (если передан): $ARGUMENTS — описание проблемы или сообщение об ошибке.

## Шаг 1: Собери контекст

Прочитай параллельно:
- `backend/.env` — переменные окружения (ключи, URL, флаги)
- `/Users/alexei.kalinin/.claude/projects/-Users-alexei-kalinin-Documents-VibeCoding-memorial-mvp/memory/session_log.md` — последние 50 строк, ищи похожие проблемы

## Шаг 2: Проверь сервисы

Выполни:
- `curl -s http://localhost:8000/api/v1/health` — backend
- `redis-cli ping` — Redis
- `curl -s http://localhost:6333/health` — Qdrant
- `ps aux | grep -E "(uvicorn|celery|vite)" | grep -v grep` — запущенные процессы

## Шаг 3: Проверь логи (если backend запущен)

Выполни: `curl -s http://localhost:8000/api/v1/health` и посмотри на детали.

Если есть описание ошибки из $ARGUMENTS — прочитай соответствующий файл:
- Ошибка в AI/chat/avatar → `backend/app/api/ai.py` + `backend/app/services/ai_tasks.py`
- Ошибка в мемориалах/медиа → `backend/app/api/memorials.py`
- Ошибка embeddings → `backend/app/services/ai_tasks.py` функции `create_embedding`, `search_similar`
- Ошибка анимации → `backend/app/services/ai_tasks.py` функции `animate_photo_did`, `animate_photo_heygen`
- Ошибка на фронтенде → `frontend/src/api/client.js` + соответствующий компонент

## Шаг 4: Сопоставь с известными паттернами

Проверь следующие частые проблемы:

**Qdrant недоступен:**
- Симптом: ошибка "Connection refused" на порту 6333
- Решение: `docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant`

**Redis недоступен:**
- Симптом: Celery не стартует, задачи не выполняются
- Решение: `brew services start redis` или `redis-server`; backend упадёт на sync fallback автоматически

**D-ID анимация не работает:**
- Симптом: статус pending вечно или ошибка 422
- Проверь: `PUBLIC_API_URL` в .env должен быть публичным URL (ngrok), не localhost
- Проверь: `DID_API_KEY` заполнен, формат `Basic <base64>`

**Embeddings не создаются:**
- Симптом: чат с аватаром отвечает "не знаю" на всё
- Проверь: `OPENAI_API_KEY` заполнен
- Проверь: Qdrant запущен
- Исправление: вызови `POST /api/v1/embeddings/rebuild/{memorial_id}`

**CORS ошибка на фронтенде:**
- Симптом: "Access-Control-Allow-Origin" в консоли браузера
- Проверь `CORS_ORIGINS` в backend/.env или backend/app/main.py

**TTS не работает (ElevenLabs):**
- Симптом: аватар отвечает текстом, аудио нет
- Проверь: `ELEVENLABS_API_KEY` заполнен
- Проверь: голос клонирован через `POST /api/v1/ai/voice/clone`

## Шаг 5: Диагноз и решение

Выведи:

**Диагноз:** (одно предложение — что именно сломано)

**Причина:** (почему это произошло)

**Решение:**
```
конкретные команды или изменения файлов
```

**Проверка:** (как убедиться что исправлено)
