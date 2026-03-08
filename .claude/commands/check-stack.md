Проверь состояние всего стека сервисов проекта memorial-mvp и дай итоговую сводку.

Выполни следующие проверки по порядку:

1. **Backend (FastAPI)**
   - Вызови GET http://localhost:8000/api/v1/health
   - Если недоступен — выведи команду для запуска

2. **Redis**
   - Выполни: redis-cli ping
   - Если недоступен — выведи команду для запуска (brew services start redis или redis-server)

3. **Qdrant**
   - Вызови GET http://localhost:6333/health или GET http://localhost:6333/collections
   - Если недоступен — выведи команду для запуска через Docker

4. **Переменные окружения**
   - Прочитай backend/.env (если существует) или backend/.env.example
   - Проверь наличие ключей: OPENAI_API_KEY, DID_API_KEY или HEYGEN_API_KEY, ELEVENLABS_API_KEY, PUBLIC_API_URL
   - Укажи какие ключи пустые или отсутствуют

5. **Celery worker**
   - Проверь запущен ли процесс: ps aux | grep celery
   - Если не запущен — выведи команду запуска

6. **Frontend**
   - Вызови GET http://localhost:5173
   - Если недоступен — выведи команду для запуска

**Итог:**
Выведи таблицу:
| Сервис | Статус | Действие |
|--------|--------|----------|

Где статус: OK / ОШИБКА / НЕ НАСТРОЕН
Где действие: что сделать если не OK.
