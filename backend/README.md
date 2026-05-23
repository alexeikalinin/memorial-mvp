# vspomin.ai - Backend

FastAPI backend для веб-сервиса хранения цифровой памяти и создания ИИ-аватаров.

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [API Endpoints](#api-endpoints)
- [Работа с Workers](#работа-с-workers)
- [Тестирование](#тестирование)
- [Развертывание](#развертывание)

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- PostgreSQL 15+ (или SQLite для разработки)
- Redis (опционально, для фоновых задач через Celery)

### Установка

1. **Клонируйте репозиторий и перейдите в директорию backend:**
```bash
cd backend
```

2. **Создайте виртуальное окружение:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив свои API ключи
```

5. **Запустите базу данных через Docker Compose:**
```bash
docker-compose up -d postgres redis
```

Или используйте локальный PostgreSQL/SQLite (см. раздел [Конфигурация](#конфигурация)).

6. **Примените миграции (если используете Alembic):**
```bash
# Пока миграции не настроены, таблицы создаются автоматически при первом запуске
# В будущем: alembic upgrade head
```

7. **Запустите сервер:**
```bash
uvicorn app.main:app --reload --port 8000
```

API будет доступен по адресу: http://localhost:8000
Интерактивная документация: http://localhost:8000/docs

## ⚙️ Конфигурация

### Переменные окружения

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

#### Обязательные для базовой работы:
- `DATABASE_URL` - URL базы данных (PostgreSQL или SQLite)
- `SECRET_KEY` - Секретный ключ для JWT (минимум 32 символа)

#### Для AI-функций:
- `OPENAI_API_KEY` - API ключ OpenAI (для LLM и embeddings)
- `DID_API_KEY` - API ключ D-ID (для анимации фото)
- `ELEVENLABS_API_KEY` - API ключ ElevenLabs (для TTS)
- `PINECONE_API_KEY` - API ключ Pinecone (для векторной БД)

#### Для хранения медиа:
- `USE_S3=false` - Использовать локальное хранилище (по умолчанию)
- Для S3: `S3_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

#### Для фоновых задач:
- `REDIS_URL` - URL Redis сервера (для Celery)

### Пример .env для локальной разработки:

```env
DATABASE_URL=sqlite:///./memorial.db
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
DEBUG=true

# Минимальная конфигурация для тестирования без AI
OPENAI_API_KEY=sk-test-key
DID_API_KEY=test-key
ELEVENLABS_API_KEY=test-key
PINECONE_API_KEY=test-key

USE_S3=false
REDIS_URL=redis://localhost:6379/0
```

## 🏃 Запуск

### Режим разработки

```bash
# Активируйте виртуальное окружение
source .venv/bin/activate

# Запустите сервер с автоперезагрузкой
uvicorn app.main:app --reload --port 8000
```

### Production режим

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Через Docker Compose

```bash
docker-compose up
```

Это запустит:
- PostgreSQL на порту 5432
- Redis на порту 6379
- Backend на порту 8000

## 📡 API Endpoints

### Health Check
- `GET /api/v1/health/` - Проверка работоспособности

### Memorials
- `POST /api/v1/memorials/` - Создать мемориал
- `GET /api/v1/memorials/{id}` - Получить мемориал
- `PATCH /api/v1/memorials/{id}` - Обновить мемориал
- `POST /api/v1/memorials/{id}/media/upload` - Загрузить медиа
- `GET /api/v1/memorials/{id}/media` - Получить все медиа мемориала
- `POST /api/v1/memorials/{id}/memories` - Добавить воспоминание
- `GET /api/v1/memorials/{id}/memories` - Получить все воспоминания

### AI
- `POST /api/v1/ai/photo/animate` - Оживить фото (D-ID)
- `POST /api/v1/ai/avatar/chat` - Чат с ИИ-аватаром (RAG)

Полная документация доступна по адресу: http://localhost:8000/docs

## 🔧 Работа с Workers

Workers обрабатывают фоновые задачи (анимация фото, создание embeddings).

### Вариант 1: Celery (рекомендуется для production)

1. **Убедитесь, что Redis запущен:**
```bash
docker-compose up -d redis
# или
redis-server
```

2. **Запустите Celery worker:**
```bash
celery -A app.workers.worker worker --loglevel=info
```

### Вариант 2: Простой worker (для разработки)

```bash
python -m app.workers.worker_simple
```

Этот worker использует polling базы данных и не требует Redis.

## 🧪 Тестирование

### Запуск тестов

```bash
pytest
```

### Тестирование API вручную

1. **Проверка health endpoint:**
```bash
curl http://localhost:8000/api/v1/health/
```

2. **Создание мемориала:**
```bash
curl -X POST http://localhost:8000/api/v1/memorials/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовый мемориал",
    "description": "Описание",
    "is_public": false
  }'
```

3. **Загрузка медиа:**
```bash
curl -X POST http://localhost:8000/api/v1/memorials/1/media/upload \
  -F "file=@/path/to/photo.jpg"
```

4. **Добавление воспоминания:**
```bash
curl -X POST http://localhost:8000/api/v1/memorials/1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Воспоминание",
    "content": "Текст воспоминания о человеке..."
  }'
```

5. **Чат с аватаром:**
```bash
curl -X POST http://localhost:8000/api/v1/ai/avatar/chat \
  -H "Content-Type: application/json" \
  -d '{
    "memorial_id": 1,
    "question": "Расскажи о детстве этого человека",
    "include_audio": false
  }'
```

## 🐳 Развертывание

### Docker

```bash
# Сборка образа
docker build -t memorial-backend .

# Запуск
docker run -p 8000:8000 --env-file .env memorial-backend
```

### Docker Compose

```bash
docker-compose up -d
```

### Production рекомендации

1. Используйте переменные окружения из секретов хостинга
2. Настройте Alembic миграции
3. Используйте S3 для хранения медиа
4. Настройте мониторинг и логирование
5. Используйте reverse proxy (nginx) перед uvicorn
6. Настройте HTTPS

## 📝 Структура проекта

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Конфигурация
│   ├── db.py                # Настройка БД
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas.py           # Pydantic схемы
│   ├── api/
│   │   ├── health.py        # Health check
│   │   ├── memorials.py     # CRUD мемориалов
│   │   └── ai.py            # AI endpoints
│   ├── services/
│   │   └── ai_tasks.py      # Интеграции с AI сервисами
│   └── workers/
│       ├── worker.py        # Celery worker
│       └── worker_simple.py # Простой worker
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔒 Безопасность

- Все API ключи хранятся в `.env` (не коммитится)
- Используйте сильные `SECRET_KEY` в production
- Настройте CORS для вашего frontend домена
- В будущем: добавьте аутентификацию и авторизацию
- Валидация всех входных данных через Pydantic

## 🐛 Отладка

### Проблемы с подключением к БД

```bash
# Проверьте, что PostgreSQL запущен
docker-compose ps

# Проверьте логи
docker-compose logs postgres
```

### Проблемы с Redis

```bash
# Проверьте подключение
redis-cli ping
```

### Логи приложения

Логи выводятся в консоль. В production настройте централизованное логирование.

## 📚 Дополнительные ресурсы

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [SQLAlchemy документация](https://docs.sqlalchemy.org/)
- [Celery документация](https://docs.celeryproject.org/)

## 🤝 Вклад

См. основной README.md проекта.

