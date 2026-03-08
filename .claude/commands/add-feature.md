Помоги добавить новую фичу в memorial-mvp. Перед работой изучи архитектуру проекта.

Прочитай следующие файлы для понимания контекста:
- CLAUDE.md — обзор архитектуры
- backend/app/models.py — модели БД (User, Memorial, Media, Memory, FamilyRelationship)
- backend/app/schemas.py — Pydantic схемы запросов/ответов
- backend/app/api/memorials.py — пример endpoint'ов (CRUD паттерн)
- frontend/src/api/client.js — все API методы на фронтенде

После изучения файлов:

**1. Планирование**
Для запрошенной фичи определи:
- Нужны ли изменения в БД (новые поля/таблицы в models.py)? Помни: таблицы создаются автоматически через Base.metadata.create_all()
- Какие новые API endpoints нужны (backend/app/api/)?
- Какие новые Pydantic схемы нужны (backend/app/schemas.py)?
- Какие изменения нужны на фронтенде (frontend/src/)?
- Нужны ли изменения в AI-сервисах (backend/app/services/ai_tasks.py)?

**2. Важные ограничения**
- owner_id=1 хардкодом — аутентификации пока нет
- Медиафайлы хранятся в backend/uploads/ и отдаются через /api/v1/media/{id}
- Для фоновых задач используй Celery (backend/app/workers/worker.py) с fallback на синхронное выполнение
- Новые роутеры регистрировать в backend/app/main.py

**3. Реализация**
- Сначала опиши план изменений по файлам
- Уточни у пользователя детали если что-то неясно
- Затем реализуй поэтапно: сначала backend (models → schemas → endpoint), потом frontend
