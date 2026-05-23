# vspomin.ai

Сервис сохранения цифровой памяти с ИИ-аватарами. Твоя память. Навсегда.

## 🎯 Цель проекта

vspomin.ai позволяет пользователям:
- Создавать мемориальные страницы
- Загружать медиа-материалы (фото, видео, аудио)
- Оживлять фотографии с помощью AI-анимации
- Добавлять текстовые воспоминания
- Общаться с ИИ-аватаром, который отвечает только на основе загруженных данных (RAG)

## 🔒 Этические принципы

- **Честность**: ИИ не выдумывает факты, отвечает только на основе предоставленных данных
- **Конфиденциальность**: Все чувствительные операции требуют подтверждений
- **Прозрачность**: Пользователь всегда знает, на основе каких данных работает ИИ

## 🛠 Технологический стек

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy (ORM)
- Alembic (миграции)
- PostgreSQL (SQLite для dev)
- Redis + Celery/RQ (очереди задач)

### AI/ML Сервисы
- OpenAI (LLM + embeddings)
- D-ID / HeyGen (photo animation)
- ElevenLabs (TTS)
- Pinecone / Qdrant (векторная БД)

### Frontend
- React (Vite)
- Минимальный UI для MVP

### Инфраструктура
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- AWS S3 / Cloudflare R2 (медиа-хранилище)

## 📁 Структура проекта

```
memorial-mvp/
├── backend/          # FastAPI приложение
├── frontend/         # React приложение
├── infrastructure/   # Deploy скрипты
└── README.md
```

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- PostgreSQL (или SQLite для dev)
- Redis (опционально, для фоновых задач)
- Docker & Docker Compose (рекомендуется)

### Локальный запуск Backend

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd memorial-mvp
```

2. Перейдите в директорию backend:
```bash
cd backend
```

3. Создайте виртуальное окружение:
```bash
python3 -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив свои API ключи
```

6. Запустите базу данных (через Docker Compose):
```bash
docker-compose up -d postgres redis
```

7. Примените миграции:
```bash
alembic upgrade head
```

8. Запустите сервер:
```bash
uvicorn app.main:app --reload --port 8000
```

9. (Опционально) Запустите worker для фоновых задач:
```bash
celery -A app.workers.worker worker --loglevel=info
```

API будет доступен по адресу: http://localhost:8000
Документация API: http://localhost:8000/docs

## 📋 План спринтов

- **Sprint 0**: Skeleton + README + .env.example ✅
- **Sprint 1**: Media upload + local storage + thumbnails
- **Sprint 2**: D-ID / HeyGen интеграция + worker + video save
- **Sprint 3**: RAG chat + Pinecone embeddings + ElevenLabs TTS
- **Sprint 4**: Frontend basic + beta testing
- **Sprint 5**: Polish, CI, docs, legal text, monetization hooks

## 📝 API Endpoints

### Health Check
- `GET /api/health/` - Проверка работоспособности сервиса

### Memorials
- `POST /api/v1/memorials/` - Создать мемориал
- `GET /api/v1/memorials/{id}` - Получить мемориал
- `POST /api/v1/memorials/{id}/media/upload` - Загрузить медиа
- `POST /api/v1/memorials/{id}/memories` - Добавить воспоминание

### AI
- `POST /api/v1/ai/photo/animate` - Оживить фото (D-ID)
- `POST /api/v1/ai/avatar/chat` - Чат с ИИ-аватаром (RAG)

## 🔐 Безопасность

- Все API ключи хранятся в `.env` файле (не коммитится в репозиторий)
- Используйте `.env.example` как шаблон
- Для production используйте секреты из переменных окружения вашего хостинга

## 📄 Лицензия

[Указать лицензию]

## 🤝 Вклад в проект

[Инструкции по контрибуции]

