# Roadmap — Memorial MVP → Product

> Обновлено: 2026-04-20  
> Статусы: `todo` | `in-progress` | `done` | `blocked`  
> Приоритеты: 🔴 критично (без этого нельзя запускать) · 🟡 важно (нужно до роста) · 🟢 рост (после первых пользователей)

---

## 🔴 КРИТИЧНО — Launch Blockers

### AUTH-1: Убрать все hardcode owner_id=1
**Статус:** `in-progress`  
**Файл:** `backend/app/api/memorials.py`  
**Что:** JWT-авторизация есть, но в ряде мест owner_id всё ещё = 1. Необходимо везде брать `current_user.id` из токена.  
**Проверить:** `grep -r "owner_id.*1" backend/app/api/`

---

### AUTH-2: Email верификация при регистрации
**Статус:** `todo`  
**Что:** После `POST /auth/register` — отправка письма с токеном. Пока не подтверждён — ограниченный доступ (нельзя создавать мемориалы и платить).  
**Нужно:** Email-провайдер (Resend / SendGrid), шаблон письма, эндпоинт `GET /auth/verify/{token}`.

---

### AUTH-3: Сброс пароля
**Статус:** `todo`  
**Что:** `POST /auth/password-reset` (запрос) + `POST /auth/password-reset/confirm` (с токеном из письма).  
**Нужно:** Email-провайдер (тот же что для AUTH-2), шаблон письма, форма в UI.

---

### AUTH-4: OAuth Google — проверить end-to-end
**Статус:** `todo`  
**Что:** В коде есть callback, но не тестировался на проде. Убедиться что `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` настроены и флоу работает.

---

### BILLING-1: Stripe Checkout — end-to-end тест
**Статус:** `todo`  
**Что:** Код checkout есть (`POST /billing/checkout`). Проверить: создаётся Session → редирект → webhook `checkout.session.completed` → `subscription_plan` в БД обновляется.  
**Тестировать:** все 5 планов (plus monthly/annual, pro monthly/annual, lifetime, lifetime_pro).

---

### BILLING-2: Stripe Webhook — полное покрытие событий
**Статус:** `todo`  
**Что:** Обработать все события по таблице в `ACCESS_LEVELS.md`:
- `invoice.payment_succeeded` → продление `plan_expires_at`
- `customer.subscription.deleted` → даунгрейд до Free
- add-on события (extra_memorial, live_session_pack)

---

### BILLING-3: Billing UI — страница управления подпиской
**Статус:** `todo`  
**Что:** Страница `/app/billing` (или модал):
- Текущий план + дата продления
- Кнопка апгрейда → Stripe Checkout
- Использование (сообщения чата, анимации) — `GET /billing/usage`
- Stripe Customer Portal для отмены/смены карты → `GET /billing/portal`

---

### SECURITY-1: Rate limiting
**Статус:** `todo`  
**Что:** Ограничить:
- `POST /auth/login` — 5 попыток/мин на IP
- `POST /ai/avatar/chat` — 60 req/мин на пользователя
- `POST /ai/photo/animate` — 10 req/мин на пользователя
- Все публичные эндпоинты — 100 req/мин на IP  
**Как:** `slowapi` (FastAPI) или nginx rate limit.

---

### SECURITY-2: Валидация загружаемых файлов
**Статус:** `todo`  
**Что:** Проверять MIME-тип по содержимому файла (не только расширению), максимальный размер по тарифу (500MB Free, 5GB Plus, 15GB Pro). Сейчас `media_service.py` проверяет ограниченно.

---

### MONITORING-1: Sentry для backend и frontend
**Статус:** `todo`  
**Что:** Добавить `sentry-sdk` в FastAPI и `@sentry/react` в Vite. Настроить алерты на 5xx и деградацию AI-сервисов. Без этого о падениях узнаём от пользователей.

---

### INFRA-1: CI/CD pipeline
**Статус:** `todo`  
**Что:** GitHub Actions:
- При PR → pytest + Playwright
- При мёрдже в main → деплой backend на Railway/Fly.io + frontend на Vercel
- Обновить `VERCEL_TOKEN` (истёк после 2026-04-01)

---

## 🟡 ВАЖНО — Core UX (до роста)

### UX-1: Onboarding для нового пользователя
**Статус:** `todo`  
**Что:** После регистрации — туториал-шаги (checklist или guided tour):
1. Создай первый мемориал
2. Загрузи фото
3. Добавь первое воспоминание
4. Попробуй чат с аватаром  
**Метрика:** % пользователей, завершивших onboarding → создавших 1 воспоминание.

---

### UX-2: Отправка инвайта по email
**Статус:** `todo`  
**Что:** Сейчас токен создаётся, но письмо не отправляется. Нужно: при `POST /invites/` автоматически слать email на указанный адрес с ссылкой `/contribute/:token`.  
**Нужно:** Email-провайдер (тот же что AUTH-2/3), шаблон.

---

### UX-3: Уведомления о новых воспоминаниях
**Статус:** `todo`  
**Что:** Когда родственник добавил воспоминание через инвайт — слать email владельцу мемориала.

---

### UX-4: Export данных мемориала
**Статус:** `todo`  
**Что:** `GET /memorials/{id}/export` → ZIP-архив: все фото/видео + воспоминания в JSON + PDF-биография (опционально). Заявлен в FAQ лендинга, в коде отсутствует.  
**Важно для:** «не боюсь потерять данные» — ключевое возражение.

---

### UX-5: Biography Agent в UI
**Статус:** `todo`  
**API есть:** `POST /api/v1/ai/biography`  
**Что нужно:** Кнопка «Сгенерировать биографию» на странице мемориала (таб или секция) → показать результат → кнопка «Сохранить как воспоминание».

---

### UX-6: Memory Quality Agent в UI
**Статус:** `todo`  
**API есть:** `POST /api/v1/ai/memory/quality`  
**Что нужно:** После добавления воспоминания — inline подсказка «Это воспоминание можно улучшить: добавьте дату / детали». В `MemoryList.jsx`.

---

### UX-7: Публичная страница мемориала — SEO
**Статус:** `todo`  
**Что:** `/m/:id` — добавить `<meta>` теги (og:title, og:image, og:description) для шэринга в соцсетях. SSR или pre-render через Vite SSG.  
**Важно для:** вирального роста через шэринг.

---

### UX-8: Мобильная адаптация — системный аудит
**Статус:** `todo`  
**Что:** Запустить `/mobile` скилл, пройтись по ключевым экранам (MemorialDetail, AvatarChat, FamilyTree, ContributePage) на реальных устройствах или BrowserStack.

---

### UX-9: Reалное demo-видео
**Статус:** `todo`  
**Что:** Записать живое видео по скрипту `frontend/landing/video/DEMO_VIDEO_SCRIPT.md`. Заменить сгенерированный `demo.mp4` на лендинге.

---

### UX-10: 404 и error страницы
**Статус:** `todo`  
**Что:** Сейчас при неверном URL или ошибке API — пустой экран. Нужны: кастомная 404, страница ошибки с кнопкой «Вернуться домой».

---

## 🟡 ВАЖНО — Технический долг

### TECH-1: Storage quota enforcement
**Статус:** `todo`  
**Что:** Лимиты хранилища (500MB Free / 5GB Plus / 15GB Pro) есть в `ACCESS_LEVELS.md`, но не реализованы в коде. Добавить счётчик в `user_usage` + проверку перед загрузкой медиа.

---

### TECH-2: Family RAG только для платных тарифов
**Статус:** `planned`  
**Что:** `include_family_memories: true` доступен всем. Ограничить: только Plus/Pro (согласно `billing.py::check_family_rag_access`).

---

### TECH-3: Provider field в модели Media
**Статус:** `idea`  
**Файл:** `backend/app/workers/worker.py:72`  
**Что:** Хранить провайдера анимации (D-ID / HeyGen) для каждого медиа, чтобы знать как отзывать/пересоздавать.

---

### TECH-4: Миграции БД (Alembic)
**Статус:** `todo`  
**Что:** Сейчас `Base.metadata.create_all()` — ок для dev, недопустимо для прода. Нужен Alembic для управляемых миграций схемы. Критично перед любым изменением модели на проде.

---

### TECH-5: Логирование структурированное
**Статус:** `todo`  
**Что:** Заменить `print()` на `structlog` / `logging` с JSON-форматом. Это нужно до Sentry и любого prod-мониторинга.

---

### TECH-6: Health check для всех внешних сервисов
**Статус:** `todo`  
**Что:** `GET /health` сейчас базовый. Расширить: проверка Qdrant, Redis, Supabase/PostgreSQL, S3. Нужно для мониторинга и автоматических рестартов.

---

## 🟢 РОСТ — После первых пользователей

### GROWTH-1: Memory Graph View (Obsidian-стиль)
**Статус:** `idea`  
**Что:** Визуализация воспоминаний и связей между людьми как интерактивный граф. Технический базис уже есть (`FamilyRelationship` edges, `FamilyNetwork.jsx`).  
**Ценность:** уникальный дифференциатор.

---

### GROWTH-2: Family Tree — кликабельные коннекторы
**Статус:** `idea`  
**Что:** В edit mode — клик по линии → попап «Удалить связь» / «Изменить тип». Сейчас управление только через список ниже дерева.  
**Технически:** добавить `edgeKey` в `orthoConnectorLines`, fat-stroke hit area, попап с DELETE + тип-селектор.

---

### GROWTH-3: Pedigree layout для семейного дерева
**Статус:** `idea`  
**Что:** Классический pedigree-режим (ancestors-only, строго влево). Базовый код уже есть (`relatives-tree` lib), UX сырой.

---

### GROWTH-4: 14-day trial для Plus
**Статус:** `idea`  
**Что:** Автоматически, без карты. После 14 дней — даунгрейд до Free или напоминание оплатить.

---

### GROWTH-5: Add-on паки в UI
**Статус:** `todo`  
**Что:** В billing UI — возможность докупить extra_memorials и live_session_pack через Stripe. Модели и Stripe события уже описаны в `ACCESS_LEVELS.md`.

---

### GROWTH-6: Публичный URL для анимации в dev (без ngrok)
**Статус:** `idea`  
**Файл:** `backend/app/workers/worker_simple.py:29`  
**Что:** Загрузка на временный S3 bucket или presigned URL — чтобы D-ID работал локально без ngrok.

---

### GROWTH-7: Аналитика использования (admin dashboard)
**Статус:** `todo`  
**Что:** Базовый admin panel: MAU, конверсия Free→Plus, топ мемориалов, расход AI-квот. Нужно для продуктовых решений.

---

### GROWTH-8: Webhook для Stripe Customer Portal
**Статус:** `todo`  
**Что:** `GET /billing/portal` → Stripe Customer Portal URL. Позволяет пользователю самому отменить / сменить карту / посмотреть историю платежей без обращения в поддержку.

---

## SEED / ДЕМО (для презентаций)

### DEMO-1: Портреты Chang/Rossi (IDs 42-56)
**Статус:** `planned`  
**Что:** Добавить `cover_photo_id` в `seed_english_portraits.py` для мемориалов Chang и Rossi.

### DEMO-2: Embeddings для Chang/Rossi воспоминаний
**Статус:** `planned`  
**Что:** Проверить и пересоздать embeddings. RAG-чат может не находить релевантный контекст для этих мемориалов.

### DEMO-3: GOT-style family tree — финальная проверка
**Статус:** `planned`  
**Что:** Открыть EN-демо (Kelly → Family), проверить GOT-стиль и Anderson stubs в правильном поколении.

---

## Порядок реализации (рекомендуемый)

```
Спринт 1 (запуск):
  AUTH-1 → AUTH-2 → AUTH-3 → BILLING-1 → BILLING-2 → BILLING-3
  SECURITY-1 → MONITORING-1 → INFRA-1

Спринт 2 (удержание):
  UX-1 (onboarding) → UX-2 (email инвайты) → UX-3 (уведомления)
  UX-4 (export) → UX-7 (SEO) → UX-8 (мобайл аудит)
  TECH-4 (Alembic) → SECURITY-2 → TECH-1 (storage quota)

Спринт 3 (монетизация):
  UX-5 (Biography UI) → UX-6 (Quality UI)
  GROWTH-4 (trial) → GROWTH-5 (add-ons UI) → GROWTH-8 (portal)
  GROWTH-7 (analytics)

Спринт 4 (рост):
  GROWTH-1 (Memory Graph) → GROWTH-2 (tree коннекторы)
  UX-9 (demo video) → AUTH-4 (Google OAuth проверка)
```

---

*Источники: `docs/MONETIZATION.md`, `docs/ACCESS_LEVELS.md`, `docs/IDEAS.md`, `docs/LANDING_FEATURES_AUDIT.md`, обсуждения в сессиях апрель 2026.*
