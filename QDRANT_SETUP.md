# 🚀 Настройка Qdrant

## Вариант 1: Qdrant Cloud (Рекомендуется для начала)

### Шаг 1: Регистрация
1. Перейдите на https://cloud.qdrant.io/
2. Зарегистрируйтесь (можно через GitHub)
3. Создайте бесплатный кластер

### Шаг 2: Получение данных
1. После создания кластера вы получите:
   - **URL**: `https://xxxxx-xxxxx.us-east-1-0.aws.cloud.qdrant.io:6333`
   - **API Key**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Шаг 3: Настройка .env
```env
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://xxxxx-xxxxx.us-east-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QDRANT_COLLECTION_NAME=memorial-memories
```

---

## Вариант 2: Qdrant локально (Docker)

### Шаг 1: Запуск Qdrant
```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

### Шаг 2: Настройка .env
```env
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Оставить пустым для локального
QDRANT_COLLECTION_NAME=memorial-memories
```

### Шаг 3: Проверка
Откройте в браузере: http://localhost:6333/dashboard

---

## Вариант 3: Qdrant локально (без Docker)

### Установка через pip (только для разработки)
```bash
pip install qdrant-client
```

Затем используйте встроенный сервер (не рекомендуется для production):
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Встроенный сервер (только для тестирования)
client = QdrantClient(":memory:")
client.create_collection(
    collection_name="memorial-memories",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)
```

---

## Проверка работы

### 1. Проверка подключения
```bash
curl http://localhost:6333/collections
```

Или для Qdrant Cloud:
```bash
curl -H "api-key: YOUR_API_KEY" \
  https://xxxxx-xxxxx.us-east-1-0.aws.cloud.qdrant.io:6333/collections
```

### 2. Проверка через Python
```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="http://localhost:6333",  # или ваш Qdrant Cloud URL
    api_key="your-api-key"  # опционально
)

# Проверка коллекций
collections = client.get_collections()
print(collections)
```

### 3. Проверка через API приложения
После запуска приложения, создайте воспоминание через API:
```bash
POST /api/v1/memorials/{id}/memories
{
  "title": "Тест",
  "content": "Это тестовое воспоминание"
}
```

Проверьте, что embedding создался:
```bash
GET /api/v1/embeddings/memorials/{id}/status
```

---

## Миграция с Pinecone на Qdrant

Если у вас уже есть данные в Pinecone:

1. **Экспорт из Pinecone** (если нужно):
   - Используйте Pinecone API для экспорта векторов

2. **Импорт в Qdrant**:
   - Создайте скрипт для переноса данных
   - Или просто пересоздайте embeddings через API:
     ```bash
     POST /api/v1/embeddings/memorials/{id}/recreate-all
     ```

---

## Устранение проблем

### Ошибка: "Collection not found"
Коллекция создается автоматически при первом использовании. Если ошибка:
1. Проверьте подключение к Qdrant
2. Проверьте права доступа (API key)
3. Проверьте URL

### Ошибка: "Connection refused"
1. Убедитесь, что Qdrant запущен (локально)
2. Проверьте URL и порт
3. Для Qdrant Cloud проверьте API key

### Ошибка: "Dimension mismatch"
Убедитесь, что используете правильную модель embeddings:
- `text-embedding-3-small` → 1536 измерений ✅
- `text-embedding-ada-002` → 1536 измерений ✅

---

## Производительность

### Рекомендации:
- **Локально**: Достаточно для разработки и небольших проектов
- **Qdrant Cloud**: Для production, лучше масштабируется
- **Размер коллекции**: Бесплатный tier Qdrant Cloud - 1GB (достаточно для ~100K векторов)

---

## Дополнительные ресурсы

- Документация Qdrant: https://qdrant.tech/documentation/
- Python клиент: https://qdrant.github.io/qdrant-client/
- Qdrant Cloud: https://cloud.qdrant.io/

