FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директории для загрузок
RUN mkdir -p uploads

# Встроенный Qdrant (qdrant-client path=...) — без отдельного процесса и без Qdrant Cloud.
# Векторы для RAG хранятся здесь; для сохранения между деплоями в Railway добавьте Volume → mount path /data
ENV QDRANT_LOCAL_PATH=/data/qdrant_storage
RUN mkdir -p /data/qdrant_storage

# Порт для FastAPI (Railway/Render передают PORT)
EXPOSE 8000
ENV PORT=8000

# Команда запуска: $PORT для облака, 8000 по умолчанию
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

