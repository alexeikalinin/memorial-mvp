Протестируй полный RAG-пайплайн чата с аватаром в memorial-mvp и выяви проблемы.

Прочитай файлы:
- backend/app/services/ai_tasks.py — функции get_embedding(), search_similar_memories(), generate_rag_response(), upsert_memory_embedding()
- backend/app/api/ai.py — endpoint POST /ai/avatar/chat

Затем выполни тесты по шагам:

**Шаг 1: Проверка данных в БД**
- Найди в memorial.db (SQLite) все мемориалы: SELECT id, name FROM memorials
- Найди воспоминания: SELECT id, memorial_id, title, embedding_id FROM memories LIMIT 10
- Сколько воспоминаний без embedding_id? Это проблема для RAG

**Шаг 2: Проверка Qdrant**
- GET http://localhost:6333/collections/memorial-memories
- Сколько векторов хранится? Совпадает ли с числом memories с embedding_id в БД?
- Если коллекция не существует — это критическая проблема

**Шаг 3: Тестовый запрос к чату**
- Возьми первый мемориал с воспоминаниями
- Отправь POST http://localhost:8000/api/v1/ai/avatar/chat с телом:
  {"memorial_id": <id>, "question": "Расскажи о себе", "include_audio": false}
- Получи ответ и проанализируй его

**Шаг 4: Анализ качества RAG**
- Были ли найдены релевантные воспоминания? (поле sources в ответе)
- Насколько ответ соответствует реальным воспоминаниям?
- Есть ли ошибки в логах?

**Итог:**
- Таблица: что работает / что нет
- Топ проблем с конкретными решениями
- Рекомендации по улучшению качества RAG (промпт, количество chunks, порог min_score)
