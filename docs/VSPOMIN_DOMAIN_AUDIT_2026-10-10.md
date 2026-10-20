# Проверка переезда vspomin.ai — 10 октября 2026

Проверка чтением production, опубликованного HTML/JS и исходников. Пользователь подтвердил успешный полный вход через Google; изменения production в этой проверке не выполнялись.

| Место | Фактическое состояние | Следующий шаг |
|---|---|---|
| Google OAuth имя | vspomin.ai, полный вход подтверждён владельцем | Готово |
| Google callback/backend PUBLIC_API_URL | https://api.vspomin.ai/api/v1/auth/google/callback / https://api.vspomin.ai | Готово |
| Главная https://vspomin.ai | HTTP200 | Домен подключён |
| Приложение https://vspomin.ai/app/ | HTTP200, title vspomin.ai — твоя память. навсегда. | Проверить функционал после CORS |
| Опубликованный SPA JS index-CctMrb9J.js | API и начало Google входа используют backend-production-e1e8.up.railway.app/api/v1 | Vercel VITE_API_URL → https://api.vspomin.ai/api/v1 и отдельная безопасная пересборка |
| Опубликованный HTML главной | Встроенный API URL backend-production-e1e8.up.railway.app/api/v1 | Включить в ту же пересборку |
| Railway FRONTEND_URL | https://memorial-mvp.vercel.app/app | После CORS вернуть вход на https://vspomin.ai/app |
| Railway PUBLIC_FRONTEND_URL | https://memorial-mvp.vercel.app | Сменить на https://vspomin.ai; проверить QR/платёжные return links |
| Railway CORS_ORIGINS | localhost:5173, memorial-mvp.vercel.app, memorial-mvp-*.vercel.app | Добавить https://vspomin.ai, сохранить старые origins для отката |
| Реальный OPTIONS с Origin https://vspomin.ai | HTTP400, без access-control-allow-origin | Подтверждает, что CORS нового сайта пока не разрешён |
| Google старый callback/authorized domain | Сохранены предыдущим этапом для отката; UI сейчас повторно не проверялся | Удалить после завершения перехода frontend; восстановление описано в runbook |
| Production /api/v1/health/ | service memorial-mvp | Локальная правка уже есть, ещё не опубликована |
| frontend/.env.example | Пример memorial-api.railway.app | Обновить справочный пример |
| Исходники CORS/.env.example | Старый Vercel оставлен рядом с новым доменом | Сохранить на переходный период |
| Seed/dev emails | demo@memorial.app, dev@memorial.app, en-demo@memorial.local | Технические демо-данные, не переименовывать реальные аккаунты без анализа |
| README/названия проекта/исторические документы | memorial-mvp остаётся | Не влияет на экран входа; отдельная уборка |

Слова memorial/memorials как английское обозначение мемориала, названия API/таблиц/компонентов — не старый бренд. Массовая замена затронет данные и маршруты, поэтому не нужна для доменного перехода.

## Безопасная последовательность следующего этапа

1. Сохранить предыдущие env (они записаны выше и в GOOGLE_AUTH_MIGRATION_RUNBOOK_2026-10-10.md). Добавить новый CORS origin, сохранив старые; проверить OPTIONS и данные с нового сайта.
2. Сменить FRONTEND_URL/PUBLIC_FRONTEND_URL, проверить Google возврат, QR и ссылки.
3. Изолированно пересобрать текущую опубликованную frontend версию с новым API адресом. Не публиковать весь текущий checkout: есть посторонние незавершённые изменения. Сохранить предыдущий Vercel deployment для rollback.
4. Проверить вход, список страниц, медиа, загрузки, приглашения, QR и тарифные переходы. Только затем убрать старые callback/authorized domain в Google. Старый Railway service-domain пока сохранить для старых ссылок и rollback.
5. Отдельно почистить справочные примеры и технические имена. Инвентаризация платёжных/почтовых кабинетов требует отдельного чтения их настроек; они в этой проверке не подтверждены.

Откат: восстановить прежние env и предыдущую frontend публикацию; старые origins/callback сохраняются до завершения проверки. Базу/секреты/службу не удалять.
