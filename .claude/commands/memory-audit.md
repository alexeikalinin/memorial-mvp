Проверь здоровье RAG-пайплайна: состояние embeddings, покрытие воспоминаний, качество векторной БД.

Аргумент (опционально): $ARGUMENTS — ID мемориала для проверки конкретного мемориала.

## Шаг 1: Проверь инфраструктуру

Выполни параллельно:
- `curl -s http://localhost:6333/health` — Qdrant работает?
- `curl -s http://localhost:6333/collections` — список коллекций
- `curl -s http://localhost:8000/api/v1/health` — backend работает?

## Шаг 2: Получи данные из БД

Выполни через backend API:

Если передан ID мемориала ($ARGUMENTS):
```
GET http://localhost:8000/api/v1/memorials/{id}/memories
```

Иначе — получи все мемориалы:
```
GET http://localhost:8000/api/v1/memorials
```
И для каждого: `GET http://localhost:8000/api/v1/memorials/{id}/memories`

## Шаг 3: Проверь embeddings в Qdrant

Прочитай `backend/app/services/ai_tasks.py` — найди функции:
- `create_embedding` / `create_memory_embedding`
- `search_similar` / `search_memories`
- Название коллекции в Qdrant (обычно `memories` или `memorial_{id}`)

Выполни: `curl -s http://localhost:6333/collections/{collection_name}` — сколько векторов хранится?

Сравни: количество воспоминаний в БД vs количество векторов в Qdrant.

## Шаг 4: Тест качества поиска

Если backend запущен — выполни тестовый запрос к чату:
```bash
curl -X POST http://localhost:8000/api/v1/ai/avatar/chat \
  -H "Content-Type: application/json" \
  -d '{"memorial_id": <id>, "message": "Расскажи о себе", "use_persona": false}'
```

Оцени ответ:
- Если ответ содержит конкретные детали из воспоминаний → RAG работает
- Если ответ общий ("Я не знаю деталей") → embeddings не созданы или поиск не находит релевантных

## Шаг 5: Найди воспоминания без embeddings

Прочитай `backend/app/models.py` — есть ли поле `embedding_created` или аналогичное у модели Memory?

Если нет — это архитектурная проблема: нет способа знать, для каких воспоминаний embedding создан.

## Шаг 6: Выдай отчёт

**Статус Qdrant:** OK / НЕДОСТУПЕН

**Статус коллекций:**
| Коллекция | Векторов | Мемориал | Воспоминаний в БД | Покрытие |
|-----------|----------|----------|-------------------|----------|

Покрытие: векторов / воспоминаний * 100%

**Проблемы:**
- ⚠️ Qdrant недоступен → все embeddings потеряны при перезапуске контейнера
- ⚠️ Покрытие < 100% → часть воспоминаний не участвует в RAG
- ⚠️ Нет поля embedding_created в модели → нет трекинга состояния
- ⚠️ Коллекция пустая → добавлены воспоминания, но embeddings не создавались

**Рекомендации:**

Если есть воспоминания без embeddings — предложи:
```bash
# Пересоздать все embeddings для мемориала
curl -X POST http://localhost:8000/api/v1/embeddings/rebuild/{memorial_id}
```

Если Qdrant хранит данные без персистентности:
```bash
# Запусти с volume для персистентности
docker run -p 6333:6333 -v $(pwd)/backend/qdrant_storage:/qdrant/storage qdrant/qdrant
```

Если нет поля трекинга embeddings — предложи добавить `embedding_status` в модель Memory (enum: pending/created/failed).
