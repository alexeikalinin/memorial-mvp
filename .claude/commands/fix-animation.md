Диагностируй проблему с анимацией фото в memorial-mvp и дай пошаговое решение.

Прочитай и проанализируй следующие файлы:
- backend/app/api/ai.py — endpoint POST /ai/photo/animate и POST /ai/animation/status
- backend/app/services/ai_tasks.py — функции animate_photo_did(), animate_photo_heygen(), get_animation_status()
- backend/app/workers/worker.py — задача animate_photo_task
- backend/.env (или .env.example) — текущие настройки

Проверь каждый пункт чеклиста:

**1. Провайдер анимации**
- USE_HEYGEN=true → используется HeyGen API
- USE_HEYGEN=false (default) → используется D-ID API
- Есть ли соответствующий API ключ (HEYGEN_API_KEY или DID_API_KEY)?

**2. PUBLIC_API_URL (критично для D-ID)**
- D-ID требует публичный URL изображения, заканчивающийся на .jpg или .png
- Если PUBLIC_API_URL пустой — D-ID НЕ будет работать локально
- Решение: настроить ngrok и поставить PUBLIC_API_URL=https://xxx.ngrok.io

**3. Redis и Celery**
- Проверь: redis-cli ping
- Проверь: ps aux | grep celery
- Без Redis задача не попадёт в очередь (есть синхронный fallback, но он медленный)

**4. Последние ошибки**
- Найди в коде все места где логируются ошибки анимации (print, logger)
- Посмотри паттерны обработки ошибок в animate_photo_did() и animate_photo_heygen()

**5. Проверка статуса задачи**
- Объясни как правильно проверять статус: POST /api/v1/ai/animation/status
- Какие поля нужны: task_id, media_id, provider

**Итог:**
1. Что скорее всего сломано (топ-3 причины)
2. Конкретные шаги для исправления каждой причины
3. Как проверить что анимация заработала
