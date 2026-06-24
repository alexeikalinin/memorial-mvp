# Session Log — Memorial MVP

> **Где хранится:** этот файл в корне репозитории — рабочая копия для Cursor/IDE. Дублирующий экземпляр: `~/.claude/projects/-Users-alexei-kalinin-Documents-VibeCoding-memorial-mvp/memory/session_log.md`. Новые записи добавлять **в начало** (после этого блока).

## [2026-06-24] Точечный security-аудит: JWT + RAG prompt injection
**Статус:** завершено ✅ (фиксы не закоммичены)

**Что делали:**
1. Изучили внешний репозиторий `mukul975/Anthropic-Cybersecurity-Skills` (817 skills для security ops) — признали избыточным для проекта целиком, но выбрали 2 точно релевантных: `testing-jwt-token-security` и `testing-prompt-injection-in-rag-pipelines`, скачали в `.claude/skills/`.
2. Прогнали `/security-review` — диффа кода не было, перешли к ручному статическому аудиту по чек-листам новых скиллов.
3. Нашли и исправили 4 риска (см. ниже). Часть находок субагента перепроверили руками и одну отбросили как false positive (invite-токены на самом деле жёстко скоплены по `memorial_id`, утечки нет).

**Проблемы и решения:**
- **Дефолтный SECRET_KEY в проде** (`config.py:21` — `"dev-secret-key-change-in-production"` как fallback). Решение: `model_validator` в `Settings` — падает при старте, если `DEBUG=false` и `SECRET_KEY` остался дефолтным.
- **RAG prompt injection** (`ai_tasks.py` — memory.content интерполировался в промпт без разделителей). Решение: явные маркеры `===BEGIN/END MEMORY DATA===` + системный промпт с инструкцией не выполнять команды из данных + функция `_sanitize_memory_text()` (regex, нейтрализует фразы типа "ignore previous instructions" / "игнорируй инструкции" оборачиванием в кавычки, не вырезая текст).
- **JWT не отзывался при смене пароля** (старый токен валиден все 7 дней после password reset). Решение: новая колонка `User.tokens_invalid_before` + `iat` в JWT (`auth.py: create_access_token`) + проверка в `_get_user_from_token` + установка в `confirm_password_reset`. Краевой случай: `iat` хранится как целые секунды, `tokens_invalid_before` — с микросекундами → токен, выпущенный в ту же секунду, ложно отклонялся. Исправлено округлением порога вниз до секунды (`invalid_before.replace(microsecond=0)`).
- **Cross-memorial утечка через `sync_family_memories`** — `memory.content` шёл в промпт GPT-анализа без санитизации, а сгенерированный `reflected_text` сохранялся в ЧУЖОЙ мемориал и показывался в UI напрямую, минуя защиту чата. Решение: `_sanitize_memory_text()` применена и на входе (memory.content), и на выходе (reflected_text).

**Изменённые файлы:**
`backend/app/config.py`, `backend/app/auth.py`, `backend/app/api/auth.py`, `backend/app/models.py`, `backend/app/main.py`, `backend/app/services/ai_tasks.py`, `docs/IDEAS.md` (добавлена SECURITY-3 deferred), `.claude/skills/testing-jwt-token-security/`, `.claude/skills/testing-prompt-injection-in-rag-pipelines/` (новые)

**Тесты:** ast.parse на все изменённые файлы + ручные integration-тесты ревокации JWT на SQLite (issue → reset → старый токен отклонён, новый принят, включая edge case с округлением секунд) — все прошли.

**Осталось сделать:**
- Закоммитить фиксы (сейчас uncommitted).
- `/code-review ultra` — широкий аудит всей кодовой базы перед продом (медиа, Stripe webhooks, CORS/rate-limiting, SQL во всех эндпоинтах, фронтенд). Сохранено как `deferred` в `docs/IDEAS.md` → SECURITY-3.
- Не реализовано (сознательно, низкий приоритет): logout-эндпоинта нет вообще (ревокация при logout не нужна без него); guardrails на выход LLM против утечки фактов другого мемориала при `include_family_memories=true`.

---

## [2026-05-23] Family RAG — ограничение по тарифу + вирусный шеринг баг
**Статус:** завершено ✅

**Что делали:**
1. Viral share в ContributePage: анонимный пользователь пытался создать новый инвайт (401). Фикс: делится той же ссылкой, по которой зашёл.
2. Family RAG guard: бэкенд правильно возвращает 402. Фронт показывал тоггл всем и глушил ошибку.

**Изменения (Family RAG):**
- `AvatarChat.jsx` — `hasFamilyRag` computed: `subscription_plan` в `['plus','pro','lifetime_pro']`
- Тоггл для Free: `disabled + opacity:0.5 + cursor:not-allowed + бейдж "Plus"`
- При 402 в чате: сбрасывает тоггл + показывает upgrade prompt (не ломаный `detail`)
- `AvatarChat.css` — `.feature-locked` + `.plan-badge` стили
- `locales/en.js` + `locales/ru.js` — 2 новых ключа: `family_locked_tooltip`, `family_upgrade_prompt`

**Изменения (viral share):**
- `ContributePage.jsx` — `handleViralShare` теперь использует `window.location.origin + /contribute/:token` вместо `invitesAPI.create()`

**Билд:** ✅ без ошибок

## [2026-05-23] Тесты email-верификации + фикс timezone-бага, все тесты 209/209 ✅
**Статус:** завершено ✅

**Что делали:**
1. Написан `tests/test_auth_email.py` — 22 теста для 4 новых auth endpoint'ов
2. Обнаружен и исправлен production-баг: SQLite возвращает naive datetime, endpoint сравнивал с `datetime.now(timezone.utc)` → `TypeError: can't compare offset-naive and offset-aware datetimes`
3. Фикс в `backend/app/api/auth.py`: нормализация tzinfo перед сравнением в `verify_email` и `confirm_password_reset`

**Изменённые файлы:**
- `backend/tests/test_auth_email.py` — новый файл, 22 теста
- `backend/app/api/auth.py` — timezone-safe сравнение в `verify_email` и `confirm_password_reset`

**Тест-покрытие:**
- `POST /auth/verify-email` — valid/invalid/expired/already-verified токен
- `POST /auth/resend-verification` — auth required / already verified / token обновляется
- `POST /auth/password-reset` — известный email / неизвестный (всегда 200) / срок токена
- `POST /auth/password-reset/confirm` — valid / invalid / expired / one-time use / new password works / old password rejected
- Full-flow: register → verify → /me | register → reset → login

**Итог:** 209/209 тестов ✅

## [2026-05-23] Supabase миграция — email verification + password reset
**Статус:** завершено ✅
**Что делали:** Применена SQL-миграция на Supabase (prod DB).
**Результат:** 5 колонок добавлены в таблицу `users`:
- `email_verified` BOOLEAN NOT NULL DEFAULT false
- `verification_token` VARCHAR(64)
- `verification_token_expires` TIMESTAMPTZ
- `password_reset_token` VARCHAR(64)
- `password_reset_token_expires` TIMESTAMPTZ
- Индексы по токенам созданы.
**Осталось:**
- ⏳ `RESEND_API_KEY` — настроить на проде (Vercel/Railway env vars) — ОТЛОЖЕНО
- ⏳ Написать тесты для auth endpoint'ов — ОТЛОЖЕНО

## [2026-05-23] Email верификация + сброс пароля (Resend)
**Статус:** завершено, тесты 187/187 ✅

**Что делали:**
1. Аудит готовности к проду: 5.5/10 — написана сводная таблица (что работает / что планировалось / что скрыть)
2. Сохранён расширенный бэклог нереализованного в `docs/IDEAS.md`
3. Реализована email-верификация + сброс пароля (провайдер: Resend)

**Backend изменения:**
- `models.py` — добавлены поля `email_verified`, `verification_token`, `verification_token_expires`, `password_reset_token`, `password_reset_token_expires` в `User`
- `config.py` — добавлены `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME`
- `services/email_service.py` — новый файл: HTML-шаблоны писем + отправка через Resend SDK
- `schemas.py` — `UserResponse` +`email_verified`; новые схемы `PasswordResetRequest`, `PasswordResetConfirm`
- `api/auth.py` — 4 новых endpoint: `POST /verify-email`, `POST /resend-verification`, `POST /password-reset`, `POST /password-reset/confirm`; регистрация теперь отправляет письмо верификации
- `requirements.txt` — добавлен `resend==2.10.0`
- `.env.example` — задокументированы новые env-переменные

**Frontend изменения:**
- `api/client.js` — 4 новых метода в `authAPI`
- `pages/VerifyEmailPage.jsx` — новая страница `/verify-email?token=...`
- `pages/ForgotPasswordPage.jsx` — новая страница `/forgot-password`
- `pages/ResetPasswordPage.jsx` — новая страница `/reset-password?token=...`
- `pages/AuthPage.css` — дополнен классами для новых страниц
- `pages/LoginPage.jsx` — ссылка "Forgot password?" + баннер успешного сброса
- `components/VerificationBanner.jsx` — мягкий баннер (не блокирует) для не-верифицированных юзеров
- `components/VerificationBanner.css` — стили баннера
- `components/Layout.jsx` — встроен `VerificationBanner`
- `App.jsx` — 3 новых маршрута: `/verify-email`, `/forgot-password`, `/reset-password`

**Поведение:**
- Регистрация → письмо уходит (если `RESEND_API_KEY` задан). Если нет — токен логируется в консоль (dev mode)
- Баннер показывается только авторизованным, не-demo юзерам с `email_verified=false`. Dismissable.
- Google OAuth → `email_verified=True` автоматически
- Сброс пароля всегда возвращает 200 (защита от перебора)
- Токены: верификация 24ч, сброс пароля 1ч

**Для активации на проде:**
1. Завести аккаунт на resend.com, получить API ключ
2. Верифицировать домен (или использовать `onboarding@resend.dev` для тестов)
3. Добавить в `.env`: `RESEND_API_KEY=re_xxx`, `EMAIL_FROM=noreply@vspomin.ai`
4. Выполнить SQL-миграцию на Supabase (см. ниже в Критический контекст)

**Миграция Supabase:**
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token_expires TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_users_verification_token ON users(verification_token);
CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users(password_reset_token);
```

**Осталось сделать:**
- Запустить Supabase миграцию перед деплоем
- Настроить `RESEND_API_KEY` в Vercel/Railway env vars
- Написать тесты для новых auth endpoint'ов

## [2026-05-23] 404 + Error Boundary
**Статус:** завершено ✅
**Изменённые файлы:**
- `frontend/src/pages/NotFoundPage.jsx` + `.css` — кастомная 404 с кнопками "← Go back" и "Home"
- `frontend/src/components/ErrorBoundary.jsx` — React class component, перехватывает render-ошибки
- `frontend/src/App.jsx` — `<Route path="*">` + `<ErrorBoundary>` обёртка
**Билд:** ✅ без ошибок

## [2026-05-23] Аудит готовности к проду
**Статус:** завершено (анализ)
**Что делали:** Полный анализ проекта — 5.5/10, таблица работающего/нереализованного, ранжирование фич по приоритету скрытия. Результат сохранён в `docs/IDEAS.md`.

## [2026-05-18] Полный аудит: тесты + бэклог + план
**Статус:** завершено

**Что делали:**
1. Запущены все pytest: 177/177 ✅ — ни одного падения
2. E2E: SKIPPED (backend + frontend не запущены)
3. Проверен hardcode owner_id=1: не осталось — JWT auth везде
4. Прочитаны IDEAS.md + ROADMAP.md — полный бэклог
5. Составлен план дальнейшей реализации

**Проблемы:**
- Багов не найдено, все тесты зелёные
- E2E не запускались (offline)
- Много deferred/planned фич которые не начинались

## [2026-05-02] Demo tutorial — 5-шаговый онбординг
**Статус:** завершено, запушено

**Что делали:**
1. Реализован `DemoTutorial` компонент (overlay + hint, шаги 1–5) — `frontend/src/components/DemoTutorial.jsx` + `.css`
2. Шаги 1–2 встроены в `DemoPage.jsx`: step 1 = overlay при первом визите, step 2 = hint после клика на семью
3. Шаги 3–5 встроены в `MemorialPublic.jsx`: переход через `?demo_step=3` в URL, step 3 = hint над чатом, step 4 = hint при переходе на Memories, step 5 = следующий hint там же
4. Прогресс сохраняется в `localStorage` (ключ `demo_tutorial_v1`)
5. E2E тест `tutorial_audit.spec.js` — 7/7 прошли со скриншотами

**Проблемы и решения:**
- CRITICAL: overlay был невидим (белый текст на белом фоне) — `:root { --surface: #FFFFFF }`, `--text-primary` не определён → fallback `#fff`. Фикс: явные цвета `#1e1c19` / `#fff` в CSS вместо переменных
- Step 3 hint уходил ниже вьюпорта (AvatarChat загружается и скроллит страницу) → добавлен `scrollIntoView` через `useEffect` в компоненте
- Step 5 содержал "ask Sean about his great-grandchildren" — имя хардкодом → заменено на нейтральное
- Тест "No tutorial when already done": `context.addInitScript` в `beforeEach` перебивал `page.evaluate` при reload → фикс: `page.addInitScript` выполняется ПОСЛЕ context-скрипта

**Изменённые файлы:**
- `frontend/src/components/DemoTutorial.jsx` — новый (с `useRef` + `scrollIntoView`)
- `frontend/src/components/DemoTutorial.css` — новый (explicit dark colors)
- `frontend/src/pages/DemoPage.jsx` — шаги 1–2
- `frontend/src/pages/MemorialPublic.jsx` — шаги 3–5, `useSearchParams`
- `e2e/tests/tutorial_audit.spec.js` — новый (7 тестов)

**Коммиты:**
- `5a8553b feat: demo tutorial — 5-step onboarding across DemoPage and MemorialPublic`
- `a59e641 fix: tutorial CSS colors explicit + step 3 scroll + step 5 generic text`

**Состояние БД (production-like):**
- 10 пользователей: 2 живых (verameeva77@mail.ru, onemmanwarrior@gmail.com, оба free, 0 мемориалов)
- ID=1 admin@memorial.app — демо-аккаунт (is_demo=True), 43 мемориала
- ID=9 1alexeikalinin1@gmail.com — аккаунт разработчика

**Осталось сделать:**
- E2E тесты с живым стеком (полный прогон)
- Полный регресс pytest (192 теста)

## [2026-04-23] Тесты биллинга и управления доступом — 67/67
**Статус:** завершено

**Что делали:**
1. Аудит покрытия тестами: обнаружили что conftest._bypass_billing глобально отключает все billing-проверки → 0 тестов биллинга
2. Создан `tests/test_billing.py` (44 теста): unit-тесты billing.py с mock User/DB
   - `_effective_plan`: free, expired plus→free, lifetime без expiry
   - `check_memorial_limit`: free=1, plus=10, extra_slots, demo bypass
   - `check_chat_quota`: free=15, plus=200, lifetime locked memorial, demo bypass
   - `check_animation_quota`: free=0→402, plus=5, pro=15, demo bypass
   - `check_tts_access`: free→402, plus/pro/lifetime OK, demo bypass
   - `check_family_rag_access`: free+lifetime→402, plus/pro OK, demo bypass
   - `check_live_session_quota`: free/plus→402, pro=5, lifetime_pro pool, demo bypass
   - Инкременты: chat, animation, live_session, lifetime_pro pool decrement
   - HTTP-level: free plan limit via API (1st OK, 2nd → 402)
   - Переопределяем autouse через `_bypass_billing` в самом test_billing.py
3. Добавлены 8 новых тестов в `tests/test_access.py`:
   - `test_reject_access_request` — reject → нет доступа
   - `test_re_request_after_rejection` — upsert после reject → PENDING
   - `test_duplicate_request_upsert` — дубль → обновление, не дублирование
   - `test_request_when_already_have_access` → 400
   - `test_non_owner_cannot_list_access` → 403
   - `test_non_owner_cannot_see_access_requests` → 403
   - `test_cannot_revoke_only_owner` → 400
   - `test_approve_already_approved_request` → 400
4. Проверен стек: backend и frontend НЕ запущены, Redis OK, Qdrant embedded (через QDRANT_LOCAL_PATH)

**Итог:** 67/67 тестов прошли. Общий счёт теперь 125+67 = 192 теста.

**Изменённые файлы:**
- `backend/tests/test_billing.py` — новый файл (44 теста)
- `backend/tests/test_access.py` — +8 тестов

**Осталось сделать:**
- Запустить полный регресс (`pytest` всей suite)
- Закоммитить все незакоммиченные изменения (33 файла + demo mode)
- Запустить E2E тесты с живым стеком

---

## [2026-04-20] Баги инвайт/биллинг исправлены + демо-режим спроектирован
**Статус:** частично завершено (баги пофикшены, демо-режим НЕ реализован — токены закончились)

**Что сделали:**
1. Исправлен CRITICAL баг: `POST /ai/avatar/chat` не проверял `is_public` → анонимы могли читать воспоминания приватных мемориалов. Добавлена проверка + `require_memorial_access(VIEWER)` для авторизованных без доступа. Файл: `backend/app/api/ai.py`
2. `uses_count` инвайта инкрементировался при каждом открытии ContributePage (`validate_invite`), а не при реальном добавлении воспоминания. Перенесён инкремент в `create_memory`. Файлы: `api/invites.py`, `api/memorials.py`
3. `source` воспоминаний теперь `"invite"` при гостевом вкладе (было всегда `"user"`). Файл: `api/memorials.py`
4. `UPGRADE_URL` исправлен с `/app/pricing` (404) на `/#pricing`. Файл: `services/billing.py`

**Демо-режим — спроектировано, не реализовано:**
- 43 демо-мемориала уже в БД (`is_public=True`, `user_id=1`, `is_demo=True`)
- 4 семьи: Kelly, Anderson, Chang, Rossi — связаны деревом + hidden connections
- Нужно: `/demo` страница (DemoPage.jsx), баннер на `/m/:id`, кнопка "Try Demo" на логине
- Подробный план в HANDOFF.md

**Изменённые файлы:**
- `backend/app/api/ai.py`
- `backend/app/api/invites.py`
- `backend/app/api/memorials.py`
- `backend/app/services/billing.py`

**Осталось сделать:** Реализовать демо-режим (см. HANDOFF.md — 4 шага)

---

## [2026-04-20] /run-tests — pytest 125/125, E2E SKIPPED (backend offline)
**Статус:** завершено
**Что делали:** Запустили полный набор тестов. pytest — все 125 прошли. E2E упали потому что бэкенд не был запущен.
**Фиксы E2E:** RegisterPage.jsx + LoginPage.jsx — добавлены атрибуты `name=` на все input'ы (без них Playwright не мог найти поля). Установлен webkit (npx playwright install webkit) — мобильные тесты больше не падают с 0ms.
**Изменённые файлы:** `frontend/src/pages/RegisterPage.jsx`, `frontend/src/pages/LoginPage.jsx`
**Следующий шаг:** Запустить бэкенд + фронт и повторить E2E.

## [2026-04-18] Роли, уровни доступа, демо-аккаунты + подготовка к Stripe

**Статус:** завершено

**Что делали:**
- Добавили поле `User.is_demo` (Boolean, default=False) в models.py — демо-аккаунты bypass биллинга
- Обновили billing.py: все 5 check-функций теперь делают ранний return для is_demo=True
- Добавили `is_demo_account()` helper в billing.py
- Обновили UserResponse в schemas.py: добавили поля `is_demo` и `subscription_plan`
- Обновили seed_ensure_owner.py: демо-юзер id=1 создаётся с `is_demo=True`
- Создали `docs/ACCESS_LEVELS.md` — исчерпывающая документация ролей × тарифов + Stripe-план
- Обновили `docs/MONETIZATION.md`: ссылка на ACCESS_LEVELS.md

**Изменённые файлы:**
- `backend/app/models.py` — +`is_demo` поле на User
- `backend/app/schemas.py` — +`is_demo`, `subscription_plan` в UserResponse
- `backend/app/services/billing.py` — +`is_demo_account()`, bypass во всех check-функциях
- `backend/seed_ensure_owner.py` — `is_demo=True` для seed-юзера
- `docs/ACCESS_LEVELS.md` — новый файл (матрица ролей × планов, Stripe-план)
- `docs/MONETIZATION.md` — ссылка на ACCESS_LEVELS.md

**Важно для деплоя:**
- Нужна DB-миграция: `ALTER TABLE users ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT false;`
- В prod поставить `is_demo=True` для `en-demo@memorial.local` и `demo@memorial.app`

**Следующий шаг:** Stripe-интеграция — `POST /billing/checkout` + webhook + `PATCH /admin/users/{id}/plan`

## [2026-04-18] Supabase Storage — завершение миграции медиа

**Статус:** завершено

**Что делали:** Завершили миграцию 43 seed-медиа на Supabase Storage.

**Контекст:** `USE_S3=true`, Supabase S3 Access Keys уже были в `.env`, bucket `memorial-media` существовал, 43 портрета уже лежали в `portraits/` Supabase. Но `file_path` в БД указывал на `uploads/xxx.jpg`, а `thumbnail_path` — на `uploads/thumbnails/...`.

**Сделано:**
1. `backend/app/api/media.py` — фикс S3 fallback: теперь приоритет `media.file_url` → не нужно конструировать URL из `file_path` (было: `get_public_url(str(media.file_path))` → неправильный URL в проде)
2. БД: обновлены все 43 Media записи — `file_path` = `portraits/name.jpg` (S3-ключ, извлечён из `file_url`)
3. Supabase: загружены 43 thumbnails в `thumbnails/` префикс; `thumbnail_path` обновлён в БД

**Итог:**
- `file_path` → S3-ключ (`portraits/...`)
- `file_url` → публичный Supabase URL
- `thumbnail_path` → S3-ключ (`thumbnails/...`)
- Все новые загрузки уже шли в S3; аудио TTS тоже

**Изменённые файлы:**
- `backend/app/api/media.py` (строки ~113-118: fallback redirect)
- БД Supabase Postgres: таблица `media`, все 43 строк

## [2026-04-15] Монетизация — Вариант C, гейтинг фич

**Статус:** завершено

**Что делали:** Выбрали и реализовали монетизационную модель Вариант C.

**Изменения:**
- `frontend/landing/index.html` — обновлены цены: Plus $7/мес ($59/год), Lifetime $99; лимиты: Free 15 msg/мес, Plus 10 мемориалов / 200 msg / 5 анимаций
- `backend/app/models.py` — добавлен `SubscriptionPlan` enum; в `User`: `subscription_plan`, `plan_expires_at`, `lifetime_memorial_id`; новая таблица `UserUsage` (счётчики по периоду YYYY-MM)
- `backend/app/main.py` — миграция новых колонок users при старте
- `backend/app/services/billing.py` — СОЗДАН: `PLAN_LIMITS`, `check_memorial_limit`, `check_chat_quota`, `check_animation_quota`, `check_tts_access`, `check_family_rag_access`, `increment_*_usage`
- `backend/app/api/ai.py` — гейты в `avatar_chat` (chat quota + family RAG + TTS), `animate_photo` (animation quota, теперь требует auth), `upload_voice` (TTS gate, теперь требует auth)
- `backend/app/api/memorials.py` — `check_memorial_limit` перед созданием мемориала
- `docs/MONETIZATION.md` — перезаписан: лимиты, архитектура гейтинга, следующие шаги

**Следующие шаги:**
1. Stripe Checkout — `POST /billing/checkout`
2. Stripe Webhook — обновление плана в БД
3. `GET /billing/usage` — endpoint для UI (показывать остаток квоты)
4. Страница `/app/pricing` в React
5. Admin endpoint для ручного апгрейда при тестировании

## [2026-04-14] Family Tree Miro-like Editor — Drag + Draw Connections + DB Storage

**Статус:** завершено

**Что делали:** Реализовали интерактивный редактор семейного дерева: перетаскивание узлов, рисование связей мышью, сохранение в БД.

**Реализовано:**
1. **Backend**: новая колонка `tree_layout_json JSON` в `Memorial`, авто-миграция в `_add_missing_columns()`, поля в `MemorialUpdate` / `MemorialResponse`
2. **Frontend — Edit Mode**: кнопка `✎ Edit layout` в тулбаре (только для generations layout). В edit mode скрывается кнопка "Add relation"
3. **Drag nodes**: `onMouseDown` на карточках → `nodeDragRef` → `onMouseMove` на канвасе обновляет `nodeOverrides` → `stopPropagation` предотвращает pan. Scale-корректировка: delta / transform.scale
4. **Effective positions**: `effectivePositions = genLayout.positions + nodeOverrides`. Все коннекторы/маркеры пересчитываются из них
5. **Автосохранение**: debounce 800ms после drag end → PATCH /memorials/{id} с tree_layout_json
6. **Port handles**: 4 точки (top/right/bottom/left) появляются при hover в edit mode
7. **Draw connections**: drag от порта → temp SVG line следует за мышью → отпускание на другой карточке → модал выбора типа связи
8. **Edge drop detection**: `data-memorial-id` атрибут на карточках + `e.target.closest('[data-memorial-id]')` в onMouseUp
9. **Pending edge modal**: модал с выбором типа связи → POST /family/relationships → reload

**Изменённые файлы:**
- `backend/app/models.py` — `tree_layout_json = Column(JSON, nullable=True)` в Memorial
- `backend/app/main.py` — ALTER TABLE в `_add_missing_columns()`
- `backend/app/schemas.py` — `tree_layout_json` в MemorialUpdate + MemorialResponse
- `frontend/src/components/FamilyTree.jsx` — всё выше + новый state + handlers
- `frontend/src/components/FamilyTree.css` — стили edit toggle, port handles, pending edge modal
- `frontend/src/locales/en.js`, `ru.js` — новые ключи: edit_mode, edit_mode_exit, connect_title

**Не реализовано (отложено):**
- Клик по коннектору для удаления связи (сложно из-за thin SVG lines; удаление через список ниже дерева)
- Сброс позиций в auto-layout (кнопка "Reset layout")

**Верификация:** `npm run build` — OK, `python -c "from app.models import Memorial..."` — OK

## [2026-04-11] Family Tree GOT-style circles + stub fix + generation positioning

**Статус:** завершено

**Что делали:** Завершили переход на GOT-style визуализацию семейного дерева (круглые аватары вместо карточек) + исправили два бага.

**Bug 1 — ft-circle-info wrong position:** Текст (имя/годы) рендерился ПОВЕРХ аватара. `top: calc(100% - 44px)` при nodeH=118 даёт top=74px, тогда как аватар заканчивается на 80px. **Решение:** inline `style={{ top: avatarSize + 4 }}` в JSX для `GenTreeNodeCard` и `StubNodeCard`, убрали неправильное CSS правило.

**Bug 2 — Anderson stubs в неправильном поколении:** `computeLayoutDepthOldestTop` помещал Андерсон-стабы в G2 (по birth_year 1865) даже если их Kelly-сосед в G3. **Решение:** В `buildGenerationLayout`, после вычисления `layoutDepth`, в singleFamilyMode пробегаем все stub-узлы и переопределяем их глубину = среднее по gen их visible (non-stub) соседей.

**Изменённые файлы:**
- `frontend/src/components/FamilyTree.jsx` — top inline style в GenTreeNodeCard и StubNodeCard
- `frontend/src/components/FamilyTree.css` — убрано неправильное CSS `top: calc(100% - 44px)`
- `frontend/src/utils/familyTreeGenerationLayout.js` — stub generation snap в singleFamilyMode

**Осталось сделать:**
- Проверить визуально в браузере (Kelly-only режим → GOT circles → Anderson stubs на правильном поколении)
- Разблокировка Anderson → должен добавиться в дерево и показать cross-family связи

---

## [2026-03-29] Перевод ContributePage на i18n

**Статус:** завершено

**Что делали:** ContributePage.jsx использовал захардкоженные русские строки — не работал в EN-режиме. Подключили `useLanguage` и вынесли все строки в локализацию.

**Изменённые файлы:**
- `frontend/src/pages/ContributePage.jsx` — подключён `useLanguage`, все строки заменены на `t('contribute.*')`
- `frontend/src/locales/en.js` — добавлена секция `contribute` (35 ключей)
- `frontend/src/locales/ru.js` — добавлена секция `contribute` (35 ключей)

---

## [2026-03-28] Avatar chat split-layout
**Статус:** завершено
**Что делали:** Реализован новый дизайн AvatarChat — split layout (левая панель с фото аватара, правая с чатом). Desktop: row, 40%/60%. Mobile ≤768px: column, фото 220px сверху.
**Изменённые файлы:** `AvatarChat.jsx`, `AvatarChat.css`, `locales/en.js`, `locales/ru.js`
**Детали:** avatar-panel с полноразмерным фото (object-fit: cover), gradient footer (имя + статус-дот), thinking overlay при loading=true. Удалено дублирующее фото/avatar из chat-header.

---

## [2026-03-28] — /run-tests (полный тест связей)
**Статус:** pytest 116/116, E2E SKIPPED (backend offline)
**Упавшие тесты:** нет
**Новый файл:** `tests/test_family_relationships_full.py` — 46 тестов по всем типам связей

---

## [2026-03-28] Расширение типов семейных связей

**Статус:** завершено

**Что делали:** Добавили 7 новых типов + CUSTOM для произвольных связей.

**Новые типы:** step_parent/step_child, adoptive_parent/adoptive_child, half_sibling, partner, ex_spouse, custom (с полем custom_label).

**Изменённые файлы:**
- `backend/app/models.py` — расширен RelationshipType enum + поле custom_label
- `backend/app/schemas.py` — custom_label в FamilyRelationshipCreate/Response
- `backend/app/api/family.py` — REVERSE_MAP/DELETE_REVERSE_MAP, валидация custom_label
- `frontend/src/components/FamilyTree.jsx` — новые типы в select (с группами), поле custom_label, маппинг в дереве
- `frontend/src/locales/ru.js` + `en.js` — переводы

**Осталось:** Миграция production БД (Supabase) — добавить enum значения + колонку custom_label

---

## [2026-03-28] Фикс тестов: 70/70 passed

**Статус:** завершено ✅

**Что делали:** Запустили все pytest-тесты, нашли 70 падений/ошибок, исправили все.

**Проблемы и решения:**

1. **bcrypt 5.0.0 + passlib 1.7.4 несовместимы** → заменили passlib в `app/auth.py` на прямые вызовы `bcrypt.hashpw`/`bcrypt.checkpw`. Ошибка `ValueError: password cannot be longer than 72 bytes` даже для коротких паролей — известный баг.

2. **Старые тесты не использовали auth** → `test_memorials.py` полностью переписан (убран свой engine, используют conftest fixtures с `auth_client`); `test_memorials_extended.py` и `test_family_tree.py` — `client` заменён на `auth_client`.

3. **invites.py** — три проблемы: `create_invite` возвращал 200 вместо 201; `revoke_invite` возвращал `{"message": ...}` 200 вместо 204; `validate_invite` не принимал `expires_at` (только `expires_days`). Исправлены все три + добавлено поле `expires_at` и `permissions` в `InviteCreate` схему.

4. **Timezone naive vs aware** — SQLite возвращает naive datetimes, сравнение с `datetime.now(timezone.utc)` бросало `TypeError`. Исправлено в `invites.py::validate_invite` и `memorials.py::create_memory` — оба используют `datetime.utcnow()` для сравнения.

5. **family.py tree builder** — не обрабатывал `CHILD` тип отношений в `children_map`, только `PARENT`. Добавлена ветка для `CHILD`: `children_map[rel.memorial_id].append(rel.related_memorial_id)`.

6. **test_update_access_role** — не регистрировал второго пользователя (нужен `second_user_headers`); использовал `grant_resp.json()["id"]` вместо `user_id` (endpoint принимает user_id, не access entry id).

7. **Тесты анонимного доступа** — `auth_client` изменяет `client.headers` in-place, поэтому "anonymous" `client` всегда имел auth-заголовок. Решение: `monkeypatch("app.auth._get_dev_user", lambda db: None)` + явный `headers={"Authorization": ""}` в запросе.

**Изменённые файлы:**
- `backend/app/auth.py` — passlib → bcrypt
- `backend/app/api/invites.py` — status_code, expires_at, 204 delete, naive datetime
- `backend/app/api/memorials.py` — naive datetime в invite validation
- `backend/app/api/family.py` — CHILD в children_map
- `backend/app/schemas.py` — expires_at + permissions в InviteCreate
- `backend/tests/test_memorials.py` — переписан с auth_client
- `backend/tests/test_memorials_extended.py` — auth_client
- `backend/tests/test_family_tree.py` — auth_client
- `backend/tests/test_access.py` — second_user_headers + monkeypatch
- `backend/tests/test_invites.py` — monkeypatch + headers

**Результат:** 70/70 pytest passed, E2E: SKIPPED (backend offline)

**Осталось сделать:**
- MemorialDetail UI: роли по `current_user_role`
- i18n: MemorialPublic и другие страницы

---

## [2026-03-28] Синхронизация с Cursor + проверка MCP

**Статус:** завершено ✅

**Что делали:**
- Проверили установленные MCP серверы в проекте → не установлено ни одного (пустой `mcpServers` в обоих конфигах)
- Получили список 9 MCP из документа пользователя; приоритет: Supabase MCP + Browser MCP
- Обновили `HANDOFF.md` с полным состоянием проекта: Фазы 1-3 авторизации, незавершённые задачи, API endpoints

**Изменённые файлы:** `HANDOFF.md`

**Осталось сделать:**
- Фаза 2: UI шаринга в MemorialDetail (accessAPI в client.js + таб "Доступ")
- Фаза 3: Запрос доступа из MemorialPublic + панель approve/reject для owner
- Установить Supabase MCP и Browser MCP

---

## [2026-03-28] Фаза 1 авторизации: JWT + MemorialAccess + frontend auth

**Статус:** завершено ✅

**Что делали:**
Реализовали полную систему аутентификации и базовой авторизации (Фаза 1 из 3).

**Backend:**
- `backend/app/auth.py` — JWT utilities: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`; FastAPI dependencies: `get_current_user` (обязательный), `get_optional_user` (опциональный), `require_memorial_access(memorial_id, user, db, min_role, allow_public)` с иерархией ROLE_PRIORITY
- `backend/app/api/auth.py` — POST /auth/register, POST /auth/token (OAuth2), POST /auth/login (JSON), GET /auth/me
- `backend/app/models.py` — добавлена `MemorialAccess(id, memorial_id, user_id, role, granted_by, created_at)` + связи в User/Memorial
- `backend/app/schemas.py` — Token, TokenWithUser, LoginRequest (размещены ПОСЛЕ UserResponse — иначе Pydantic v2 падал с forward ref error); MemorialDetailResponse.current_user_role
- `backend/app/api/memorials.py` — убран `owner_id=1` везде; `create_memorial` auto-creates `MemorialAccess(OWNER)`; все write-endpoints защищены; read-endpoints используют `get_optional_user + allow_public=True`; `create_memory` поддерживает `?invite_token=` (проверяет MemorialInvite) для анонимных вкладчиков
- `backend/app/main.py` — убран `_ensure_default_user()`, добавлен `_migrate_existing_access()` (создаёт OWNER записи для существующих мемориалов при старте), добавлен auth router
- `backend/app/config.py` — ACCESS_TOKEN_EXPIRE_MINUTES=10080 (было 30)

**Frontend:**
- `frontend/src/context/AuthContext.jsx` — AuthProvider + useAuth hook; при монтировании читает localStorage → /auth/me для верификации
- `frontend/src/components/ProtectedRoute.jsx` — redirect /login если нет user
- `frontend/src/pages/LoginPage.jsx` + `RegisterPage.jsx` + `AuthPage.css` — формы входа/регистрации
- `frontend/src/App.jsx` — AuthProvider wrapper, /login и /register публичные, / /memorials/new /memorials/:id защищены через ProtectedRoute
- `frontend/src/api/client.js` — Bearer token interceptor (читает из localStorage), добавлены authAPI + createMemory принимает inviteToken
- `frontend/src/components/Layout.jsx` — показывает username + кнопку Выйти если авторизован, иначе Войти/Регистрация
- `frontend/src/pages/ContributePage.jsx` — передаёт `token` в `createMemory(..., token)`

**Проблемы и решения:**
- Pydantic v2 forward ref error: `TokenWithUser` ссылался на `"UserResponse"` строкой, но класс не был ещё определён. Решение: разместить Token schemas ПОСЛЕ UserResponse.
- `_migrate_existing_access`: нужно LEFT OUTER JOIN на условии `(memorial_id=X AND role=OWNER)` + `WHERE access.id IS NULL` — работает в SQLAlchemy через `.outerjoin(MemorialAccess, condition)`.

**Изменённые файлы:** см. HANDOFF.md

**Осталось сделать:**
- Фаза 2: `backend/app/api/access.py` + защита family.py/invites.py + UI шаринга в MemorialDetail
- Фаза 3: AccessRequest модель + "Запросить доступ" UI
- MemorialDetail: UI должен показывать owner-панель только при `current_user_role === 'owner'`

---

## [2026-03-25] E2E: семейный RAG — 5 пар, чеклист с ответами API

**Статус:** завершено (прогон на локальном backend + реальные ответы чата)

**Что делали:**
- Подобраны 5 пар (B=аватар, A=чужой мемориал с упоминанием B, ребро `family_relationships`: B→A).
- Выполнены `POST /api/v1/ai/avatar/chat` с `include_family_memories=true` (без аудио).
- Зафиксированы вопросы, ответы, оценки 1–5 соответствия опорному воспоминанию.

**Результат:** средняя оценка **4.6/5**; тесты 3 и 5 — частичное обобщение LLM (детали сида не дословно).

**Файл:** [docs/CROSS_MEMORIAL_RAG_CHECKS.md](docs/CROSS_MEMORIAL_RAG_CHECKS.md)

**Изменённые файлы:** `docs/CROSS_MEMORIAL_RAG_CHECKS.md` (новый), `SESSION_LOG.md`

---

## [2026-03-25] ENVIRONMENT.md: локально vs веб, MCP, Playwright

**Статус:** завершено

**Что делали:**
- Проверка MCP: в репозитории нет `mcp.json`; глобальный список MCP Cursor с диска не извлечён (конфиг в UI Cursor). Рекомендации: Git/GitHub, SQLite (read-only к `memorial.db`), опционально `@playwright/mcp` — зафиксированы в [ENVIRONMENT.md](ENVIRONMENT.md).
- Добавлен [ENVIRONMENT.md](ENVIRONMENT.md) — таблица локально/прод, `VITE_API_URL` vs прокси Vite, `backend/.env` (`DATABASE_URL`, `USE_S3`, `CORS_ORIGINS`, `PUBLIC_*`, `BOT_API_BASE_URL`), Qdrant, чеклист деплоя, раздел MCP.
- **Открытые вопросы / нерешённое:** пользователь сам проверяет в Cursor Settings → MCP, какие серверы реально включены; при деплое — актуализировать `VITE_API_URL` на Vercel и переменные Railway/бэкенда (не автоматизировалось).

**Изменённые файлы:**
- `ENVIRONMENT.md` — новый
- `SESSION_LOG.md` — эта запись

**Playwright:** ассистент может писать тесты на Playwright и использовать MCP `@playwright/mcp`, если пользователь добавит его в конфиг Cursor; в этом чате инструментов браузера по умолчанию может не быть.

---

## [2026-03-18] ElevenLabs ключ #3, краткие ответы аватара, аудио по умолчанию

**Статус:** завершено

**Что делали:**
- `backend/.env` — заменён `ELEVENLABS_API_KEY` на новый ключ #3
- `backend/app/services/ai_tasks.py` — промпт аватара на краткость (1–3 предложения), `max_tokens` 800→200
- `frontend/src/components/AvatarChat.jsx` — `includeAudio` по умолчанию `true`

**Изменённые файлы:** см. `HANDOFF.md` в корне (дата 2026-03-18).

---

## [2026-03-17] Питч-демо: QR-код inline display

**Статус:** завершено ✅

**Что делали:**
Реализовали inline отображение QR-кода для питч-демо (шаг 5 сценария: «Покажи QR-код на экране»).

**Изменения:**
1. `MemorialDetail.jsx` — кнопка «QR-код» теперь открывает модал с инлайн-изображением QR (220×220px), URL публичной страницы + кнопка «Копировать» + кнопка «Скачать PNG». Добавлено состояние `showQRModal`, `qrBlobUrl`, `qrLoading`.
2. `MemorialDetail.css` — новые стили `.qr-modal`, `.qr-modal-body`, `.qr-image`, `.qr-hint`, `.qr-url-row`, `.qr-url`.
3. `MemorialPublic.jsx` — добавлена секция «Поделиться QR-кодом» перед footer: кнопка → раскрывающийся панель с QR-изображением + URL + копировать + скачать. Переработан `handleDownloadQR` → `handleShowQR` + отдельный `handleDownloadQR`.
4. `MemorialPublic.css` — новые стили `.public-share-section`, `.btn-share-qr`, `.public-qr-panel`, `.public-qr-image`, `.public-qr-hint`, `.public-qr-url-row`, `.btn-copy-small`, `.btn-download-qr`.

**Проверка:** `npm run build` — ✅ 687ms, без ошибок.

**Изменённые файлы:**
- `frontend/src/pages/MemorialDetail.jsx`
- `frontend/src/pages/MemorialDetail.css`
- `frontend/src/pages/MemorialPublic.jsx`
- `frontend/src/pages/MemorialPublic.css`

---

## [2026-03-17] FamilyTree — полное имя + контраст живые/умершие

**Статус:** завершено ✅

**Что делали:**
- `NODE_W` 150→172, `NODE_H` 88→108 — место для полного ФИО
- `.ft-node-name` — убран `-webkit-line-clamp`, `word-break: break-word` — имя полностью
- `.ft-node--deceased` — тёмная карточка (bg rgba(38,30,24,0.88)), grayscale 60%, opacity 0.80; текст приглушён
- `.ft-node` — убран `overflow: hidden` чтобы имя не обрезалось по высоте
- `.ft-node-years` — font-weight 500 для читаемости дат

**Изменённые файлы:**
`frontend/src/components/FamilyTree.jsx` (NODE_W, NODE_H), `frontend/src/components/FamilyTree.css`

**Осталось:** Визуальная проверка

## [2026-03-17] FamilyTree — H-bracket коннекторы

**Статус:** завершено ✅

**Что делали:**
Заменили bezier-кривые «веер» на стандартный genealogy H-bracket паттерн в `ConnectionLines`.

**Изменения:**
- `V_GAP`: 100 → 120 (место для шины)
- `SPOUSE_GAP`: 16 → 20
- `BUS_DROP = 32` — новая константа (стем от knot до горизонтальной шины)
- Логика parent-child: вместо bezier от knot к каждому ребёнку отдельно — группировка детей по pairKey, затем: стем вниз от knot → горизонтальная шина → вертикальные дропы к каждому ребёнку
- Одиночный родитель (без пары): polyline с прямым углом через midY
- Линия супругов: `strokeWidth` 2.5, цвет `rgba(220,195,150,0.9)`, убран символ ∞ (заменён на `<title>Супруги</title>`)
- Knot-ромб: size 6 → 8px, `strokeWidth` 1 → 1.5

**Изменённые файлы:** `frontend/src/components/FamilyTree.jsx`

**Осталось сделать:** Визуальная проверка в браузере (npm run dev → localhost:5173 → мемориал → Семья)

## [2026-03-16] UI Редизайн «Warm Heritage 2.0» — полный цикл

**Статус:** завершено ✅

**Что делали:**
Реализовали полный редизайн CSS всех 13 файлов по плану «Warm Heritage 2.0». Только CSS, JSX не трогали.

**Ключевые изменения:**
1. `index.css` — новые токены (`--color-surface-hero`, `--color-accent-warm`, `--color-accent-light`, `--color-border-strong`, `--font-display`, `--font-body`, z-index система), `.btn-ghost`, улучшен `:focus-visible`, типографика h1-h4 с explicit line-height
2. `Layout.css` — underline анимация `scaleX 0→1`, отключён blur на мобиле, footer padding 2rem
3. `Home.css` — amber overlay, subtitle opacity 0.7, grid minmax 300px, card-name 1.4rem, card-dates 1rem, hover border-left accent, warm overlay на hover cover
4. `MemorialDetail.css` — теплее hero gradient, letter-spacing на name 0.02em, более заметные btn-icon с accent border, tabs 3px indicator + hover bg
5. `MemorialPublic.css` — memory card border-left 4px, photos grid 220px, contribute CTA с accent gradient border
6. `MemorialCreate.css` — form top border 3px accent-dark, select arrow accent-dark
7. `AvatarChat.css` — **КЛЮЧЕВОЕ**: переход на светлую тему (bg=surface, header=surface-warm, input=surface). Fullscreen сохраняет тёмную тему через `.avatar-chat--fullscreen` оверрайды.
8. `MediaGallery.css` — media item bg=surface-warm, audio placeholder warm, media actions bg=surface с border
9. `MemoryList.css` — border-left gradient (accent→accent-light), share panel в accent тонах вместо зелёного, btn-share в accent стиле
10. `FamilyTree.css` — **КЛЮЧЕВОЕ**: canvas bg тёмный коричнево-янтарный (`#1C1917→#5C3D22`), упрощены звёзды до 3 точек + warm dust, grayscale(40%) для deceased
11. `HiddenConnections.css` — весь UI переведён в светлую тему (surface-warm), hop colors → тёплая шкала (accent/accent-warm/amber/muted)
12. `LifeTimeline.css` — dot hover scale 1.5, card hover border-left accent, mobile year label fix
13. `ContributePage.css` — active tab box-shadow

**Проблем не было** — чистые CSS-изменения без затрагивания JSX/функционала.

**Изменённые файлы:**
`frontend/src/index.css`, `frontend/src/components/Layout.css`, `frontend/src/pages/Home.css`, `frontend/src/pages/MemorialDetail.css`, `frontend/src/pages/MemorialPublic.css`, `frontend/src/pages/MemorialCreate.css`, `frontend/src/components/AvatarChat.css`, `frontend/src/components/MediaGallery.css`, `frontend/src/components/MemoryList.css`, `frontend/src/components/FamilyTree.css`, `frontend/src/components/HiddenConnections.css`, `frontend/src/components/LifeTimeline.css`, `frontend/src/pages/ContributePage.css`

**Осталось сделать:** Визуальная проверка в браузере (npm run dev → localhost:5173)

## [2026-03-16] Склонение имён + фиксы видимости чата

**Статус:** завершено ✅

**Что делали:**
1. Создан `frontend/src/utils/declension.js` — утилита склонения русских имён (предложный + творительный падеж)
2. `MemoryList.jsx` — импорт `aboutName`, склонение в 3 местах (сообщение для шеринга, заголовок share, панель с приглашением)
3. `AvatarChat.jsx` — импорт `instrumentalName`, "Чат с Светланой Николаевной Морозовой" вместо именительного
4. `AvatarChat.css` — `.suggested-btn` стал видимым на светлом фоне: `bg=surface-warm`, `border=border-strong`, `color=accent-dark`
5. `MemorialDetail.css` — `.memorial-description` изменён с italic serif на `font-sans; font-style:normal; color: var(--text)` для читаемости

**Изменённые файлы:**
- `frontend/src/utils/declension.js` — новый файл
- `frontend/src/components/MemoryList.jsx` — import + 3 места склонения
- `frontend/src/components/AvatarChat.jsx` — import + instrumentalName в заголовке чата
- `frontend/src/components/AvatarChat.css` — `.suggested-btn` видимость
- `frontend/src/pages/MemorialDetail.css` — `.memorial-description` читаемость

---

## [2026-03-16] Тестирование голосовых аватаров + документация фичи

**Статус:** завершено ✅

**Что делали:**
Протестировали разделение голосов по полу аватара. Подтверждено рабочим:
- Мужской мемориал (`voice_gender=male`) → ElevenLabs голос `pNInz6obpgDQGcFmaJgB` (Adam)
- Женский мемориал (`voice_gender=female`) → ElevenLabs голос `EXAVITQu4vr4xnSDxMaL` (Bella)
- Фронтенд отправляет поле `include_audio` (не `generate_audio`!) в запросе

**Документация:** `VOICE_FEATURE.md` в корне проекта — полная шпаргалка по фиче:
точные файлы/строки, curl-тесты, таблица поломок и решений. Если голоса сломались после дизайн-изменений — смотреть туда.

**Ключевые файлы фичи:**
- `backend/app/api/ai.py` ~459–500 — логика выбора голоса
- `backend/app/services/ai_tasks.py` — функция `generate_speech_elevenlabs`
- `backend/app/schemas.py` — `AvatarChatRequest.include_audio`
- `frontend/src/components/AvatarChat.jsx` ~218, ~493 — отправка и рендер аудио
- `backend/.env` — `ELEVENLABS_VOICE_ID_MALE/FEMALE`

**Изменённые файлы:**
- `VOICE_FEATURE.md` — создан (документация)

---

## [2026-03-16] Полное наполнение воспоминаний всех 21 участника

**Статус:** завершено ✅

**Что делали:**
Изучили архитектуру family sync / relative memories (два механизма):
1. Query-time расширение поиска (`include_family_memories=True`) — ищет по Qdrant с фильтром всех родственников
2. Sync-агент (`POST /api/v1/ai/family/sync-memories/{id}`) — GPT-4 ищет упоминания родственников в воспоминаниях и создаёт отражённые Memory записи с `source="family_sync"`

Написан `backend/seed_memories_full.py` — добавляет полноценные воспоминания от детства до смерти/настоящего:
- Каждый из 21 участника получает 4-7 воспоминаний, охватывающих детство, юность, зрелость, старость
- Воспоминания содержат явные упоминания родственников по имени → работает family sync
- Скрипт идемпотентен (проверяет дубли по заголовку)

**Изменённые файлы:**
- `backend/seed_memories_full.py` — новый файл

**Следующий шаг:**
1. Запустить `python seed_memories_full.py` (нужен работающий Qdrant + OpenAI key)
2. Запустить family sync для ключевых мемориалов через POST /api/v1/ai/family/sync-memories/{id}

---

## [2026-03-16] Фото мемориалов + семейное дерево (pan/zoom + bidirectional)

**Статус:** завершено ✅

### 1. Фотографии мемориалов — исправление

**Проблема:** Изображения не отображались (broken image на главной и в деталях).

**Причина:** `USE_S3=true` → backend делает `RedirectResponse` на Supabase Storage URL. Скрипты сохраняли файлы **локально** в `backend/uploads/`, а не в Supabase. URL вида `supabase.co/storage/.../uploads/xxx.jpg` давал 400.

**Решение:**
1. `backend/fix_memorial_photos.py` — исправлен SSL баг (заменили `urllib.request` на `requests` библиотеку), скачал age/gender matched портреты с randomuser.me для мемориалов 20-31 (european nationalities: gb,ie,au,nz,fi,no,dk,nl)
2. `backend/fix_photos_tpdne.py` — новый скрипт для мемориалов 32-42, использует thispersondoesnotexist.com (AI-generated реалистичные лица) — randomuser.me заблокировал по rate-limit после 12 запросов (seed `d3adb33f` = error маркер)
3. `backend/upload_portraits_to_supabase.py` — загрузил все 23 локальных файла в Supabase Storage bucket `memorial-media` по ключу `uploads/{filename}.jpg`

**Итог:** media.id 11-33, все 23 мемориала (ID 20-42) имеют cover_photo, файлы в Supabase.

**Изменённые файлы:**
- `backend/fix_memorial_photos.py` — urllib→requests, SSL fix
- `backend/fix_photos_tpdne.py` — новый (thispersondoesnotexist.com)
- `backend/upload_portraits_to_supabase.py` — новый (upload to S3)

---

### 2. Семейное дерево — полный рефакторинг

**Проблема:** Старое дерево показывало только потомков от выбранного человека. Нет предков. Нет pan/zoom. Не работало слияние семей.

**Решение:**

**Backend** — новый endpoint `GET /family/memorials/{id}/full-tree?max_depth=6`:
- BFS по ВСЕМУ графу связей (не только потомки, но и предки)
- Каждому узлу присваивается **generation**: 0=root, -1=родители, -2=деды, +1=дети, +2=внуки
- Логика BFS: `parent` edge → generation-1, `child` → generation+1, `spouse/sibling` → то же поколение
- Возвращает плоский граф: `{ nodes: [...], edges: [...], root_id }`
- Схемы: `FullTreeNode`, `FullTreeEdge`, `FullFamilyTreeResponse` добавлены в `schemas.py`
- Слияние семей: если два дерева имеют общего предка — граф автоматически соединяется (BFS проходит через все связи в БД)
- Проверено: для мемориала 42 возвращает 21 узел, 41 ребро

**Frontend** — полный рерайт `FamilyTree.jsx` + `FamilyTree.css`:
- **Pan**: drag мышью + onTouchStart/Move одним пальцем
- **Zoom**: колёсико мыши (relative to cursor point) + pinch двумя пальцами (relative to pinch center)
- **Centration**: при загрузке автоматически центрируется на root node через `useEffect`
- **Layout**: `computeLayout()` группирует узлы по generation, в каждой строке — равномерное распределение
- **SVG overlay**: кривые Безье для parent-child линий, горизонтальные линии для супругов/сиблингов
- **Root node**: золотая рамка + цветная полоска сверху + двойной ring
- **Deceased nodes**: grayscale filter
- Тёмное небо со звёздами (signature canvas) сохранено

**Добавлен API метод** в `frontend/src/api/client.js`:
```js
getFullTree: (memorialId, maxDepth = 6) =>
  apiClient.get(`/family/memorials/${memorialId}/full-tree`, { params: { max_depth: maxDepth } }),
```

**`npm run build` ✅** — 721ms, без ошибок.

**Изменённые файлы:**
- `backend/app/schemas.py` — добавлены FullTreeNode, FullTreeEdge, FullFamilyTreeResponse
- `backend/app/api/family.py` — добавлен endpoint `full-tree`
- `frontend/src/api/client.js` — добавлен `getFullTree`
- `frontend/src/components/FamilyTree.jsx` — полный рерайт (pan/zoom canvas)
- `frontend/src/components/FamilyTree.css` — полный рерайт

**Известные ограничения / что можно улучшить:**
- Layout не оптимизирован: дети не центрируются под родителями (простое равномерное распределение по генерации). Можно улучшить алгоритмом Reingold-Tilford
- При большом дереве (50+ узлов) может быть перегружено — нужна виртуализация или level-of-detail
- Нет анимации перехода при смене центра (центрирование мгновенное)

---

## [2026-03-16] Редизайн UI — концепция "Тихий свет"

**Статус:** в процессе (6/9 файлов CSS завершено, ПРЕРВАН из-за лимита токенов)

**Что делали:**
Полный редизайн фронтенда. Концепция: "Тихий свет" — тёплая, не депрессивная палитра.
Дизайн-система: CSS-переменные в `index.css`, шрифты Cormorant Garamond + Inter (Google Fonts).

**Палитра:**
- `--bg: #FAF8F5`, `--surface-dark: #1C1917`
- `--accent: #C4A882` (золотисто-бежевый), `--accent-dark: #8B5E3C` (янтарь)
- `--border: #E8E0D4`, `--text: #3D3631`, `--text-muted: #8C7E6E`

**Изменённые файлы (ЗАВЕРШЕНО):**
- `frontend/src/index.css` — CSS vars, Google Fonts, base, buttons, form, animations
- `frontend/src/components/Layout.css` + `Layout.jsx` — sticky blur navbar, scroll state
- `frontend/src/pages/Home.css` + `Home.jsx` — hero dark + scroll cue + карточки с cover strip
- `frontend/src/pages/MemorialCreate.css` + `MemorialCreate.jsx` — centered card form
- `frontend/src/pages/MemorialDetail.css` + `MemorialDetail.jsx` — full-width hero overlay, новые tabs
- `frontend/src/components/AvatarChat.css` — тёмный чат, amber кнопки, cream пузыри
- `frontend/src/components/MemoryList.css` — gold left-border карточки
- `frontend/src/components/MediaGallery.css` — тёмный grid с hover zoom

**ОСТАЛОСЬ ДОДЕЛАТЬ (следующая сессия):**
1. `frontend/src/components/LifeTimeline.css` — золотая вертикальная линия, alternating layout
2. `frontend/src/components/FamilyTree.css` — warm cream nodes, accent lines
3. `frontend/src/pages/MemorialPublic.css` — read-only версия мемориала
4. `frontend/src/pages/ContributePage.css` — форма гостя
5. `frontend/src/components/HiddenConnections.css` — новый компонент
6. Проверить и починить если что-то сломалось в MemorialDetail.jsx (закрывающие теги + formatYear объявлен внутри return)

**Важный баг для проверки:**
В `MemorialDetail.jsx` функция `formatYear` объявлена внутри return JSX — нужно проверить что она перед return (возможно редактирование сместило код).



## [2026-03-15] Supabase интеграция + RAG фикс + деплой

**Статус:** завершено (остался 1 шаг — Vercel VITE_API_URL)

**Что делали:**

### 1. Дубликаты мемориалов — очистка SQLite
- Seed скрипт запускался 4 раза → 51 мемориал вместо 21
- Оставили IDs 1-21, удалили 22-51 (вместе с memories и family_relationships)
- cover_photo_id указывал на дублированные media (11-20) → исправили на оригинальные (1-10)

### 2. Supabase PostgreSQL
- Project ref `abbpyojdtlzkijcgmjzh` найден в `.claude/settings.local.json`
- Пароль сброшен → `AdcXpru0akzE2G6B`
- DATABASE_URL → Supabase Transaction Pooler (`aws-1-eu-central-1.pooler.supabase.com`)
- `db.py`: pool_pre_ping=True, pool_size=5, pool_recycle=300 для pgBouncer
- Работает: Railway отдаёт 10 мемориалов из Supabase

### 3. Supabase Storage (S3)
- Bucket `memorial-media` (PUBLIC, any MIME, 50MB Free tier)
- `config.py`: SUPABASE_URL, `s3_endpoint_url`, `supabase_public_url` properties
- `s3_service.py`: Supabase S3 endpoint + `get_public_url()`
- `media.py`: `RedirectResponse` на Supabase публичный URL при USE_S3=true (использует `media.thumbnail_path` из БД)
- `memorials.py`: thumbnails тоже идут в S3

### 4. Qdrant кластер
- eu-west-2 (`1a6a0d99`) → мёртв (404)
- Переключились на us-east-1 (`591a5520`) — работает
- `QDRANT_LOCAL_PATH` очищен

### 5. Embeddings — полное пересоздание
- 168 воспоминаний, только 14 имели embedding_id
- Коллекция пересоздана, все 168/168 embeddings созданы успешно

### 6. RAG chat — два фикса
**Фикс 1:** `qdrant-client 1.7.0` — `client.search()` удалён в 1.7+
- Обновили до `1.17.1`, заменили на `client.query_points()` в `ai_tasks.py`

**Фикс 2:** `min_score=0.5` — слишком высокий для text-embedding-3-small
- text-embedding-3-small даёт score 0.2-0.4 для релевантных текстов
- Снизили до `min_score=0.2`
- Проверено: для Анны Морозовой находит 3 воспоминания со score 0.38-0.47

### 7. Railway
- Все env vars обновлены через `railway variables set`
- `railway up --detach` — новый код задеплоен

**Изменённые файлы:**
`backend/.env`, `config.py`, `db.py`, `s3_service.py`, `media.py`, `memorials.py`, `ai_tasks.py`, `requirements.txt`

**Осталось сделать:**
- [ ] **КРИТИЧНО:** Vercel → Environment Variables → `VITE_API_URL=https://backend-production-e1e8.up.railway.app/api/v1` → Redeploy
- [ ] Фотографии в мемориалах Supabase: cover_photo_id=null у большинства (нет медиа — нужно залить фото)
- [ ] Проверить дубликаты в Supabase DB (там могут быть старые сиды)

## [2026-03-15] Фикс: аватарки мемориалов не отображались нигде

**Статус:** завершено

**Что делали:**
- Диагностировали, почему все изображения (главная, шапка мемориала, чат) показывали broken image
- Бэкенд: `USE_S3=true`, `DATABASE_URL` = Supabase PostgreSQL
- Реальный thumbnail_path в DB: `memorials/{id}/thumbnails/{uuid}_{name}_medium.jpg`
- Код в `media.py` вычислял: `{parent}/{stem}_{size}.jpg` = `memorials/{id}/{uuid}_{name}_small.jpg`
- Результат: URL без `thumbnails/` папки и с неверным суффиксом → 404 на Supabase

**Решение:**
- `media.py`: вместо вычисления thumb_key — использовать `media.thumbnail_path` из БД напрямую
- Если `thumbnail_path` есть → редирект на него; иначе → редирект на оригинальный файл

**Изменённые файлы:**
- `backend/app/api/media.py` — исправлена логика построения S3 ключа для миниатюр

**Проверено:** curl `media/1?thumbnail=small` → 302 на правильный Supabase URL → 200

---

## [2026-03-15] Оптимизация переключения вкладок + аватарки в семейном дереве

**Статус:** завершено

**Что делали:**
1. Убрали медленное пересоздание компонентов при смене вкладок — lazy mounting через `mountedTabs` Set
2. Исправили отсутствие фото в семейном дереве — бэкенд возвращал относительный URL (`/api/v1/media/...`), который в продакшне (Vercel+Railway) указывал на Vercel, а не на бэкенд
3. Оптимизировали N+1 запросы в `build_tree` — теперь 3 запроса вместо N*2+

**Проблемы и решения:**
- `cover_photo_url` в `FamilyTreeNode` хранил относительный URL вместо ID — заменили на `cover_photo_id` (int), фронтенд сам строит URL через `getMediaUrl()`
- `build_tree` делал по 1+ запросу на каждый узел — переписан на BFS: сначала собираем все ID, потом 1 батч-запрос для мемориалов, 1 для связей, дерево строим в памяти

**Изменённые файлы:**
- `backend/app/schemas.py` — `FamilyTreeNode`: заменено `cover_photo_url: str` → `cover_photo_id: int`
- `backend/app/api/family.py` — `get_family_tree`: bulk queries (BFS + 2 batch queries), убраны N+1 вызовы
- `frontend/src/components/FamilyTree.jsx` — импорт `getMediaUrl`, использование `node.cover_photo_id` вместо `node.cover_photo_url`
- `frontend/src/pages/MemorialDetail.jsx` — lazy mounting (`mountedTabs` Set), компоненты вкладок больше не перемонтируются

**Осталось сделать:** нет



## [2026-03-15] Фикс семейных деревьев + нативный фильтр Qdrant + cross-memorial RAG

**Статус:** завершено

**Что делали:**
1. Диагностировали и исправили критический баг в `build_tree` (`family.py`)
2. Добавили нативный Qdrant фильтр с `MatchAny` вместо Python-фильтрации
3. Создали payload index на поле `memorial_id` в Qdrant Cloud
4. Исправили `loadAvailableMemorials` в FamilyTree.jsx (заглушка → реальный API)
5. Заменили `input[type=number]` для ID на `select` с именами мемориалов

**Критический баг: build_tree (family.py)**
- Проблема: `build_tree` искал `CHILD` отношения от текущего узла, чтобы найти детей
- Семантика: `memorial_id=A, type=CHILD, related_memorial_id=B` = "A является ребёнком B"
  → дерево показывало РОДИТЕЛЕЙ как детей и не показывало реальных детей вообще
- Исправление: заменил `RelationshipType.CHILD` на `RelationshipType.PARENT`
  → `type=PARENT` значит "A является родителем B" — это правильный запрос для поиска детей
- Файл: `backend/app/api/family.py`

**Пример правильного дерева (после фикса):**
- Иван Морозов (3) ∞ Анна (4) → дети: Николай (5), Мария (6)
  - Николай (5) ∞ Людмила (10) → дети: Светлана (20), Александр (21)
- Фёдор Ковалёв (7) ∞ Прасковья (8) → дети: Пётр (9), Людмила (10)
  - Людмила ∞ Николай → дети: Светлана (20), Александр (21) [cross-family]

**Qdrant: призрачные embeddings и нативный фильтр:**
- В Qdrant Cloud 168 точек, но 30 из удалённых мемориалов (ID=11: 9шт, ID=12: 21шт)
- Старая реализация: Python-фильтрация после запроса без фильтра → призрачные embeddings занимали слоты
- Новая реализация: `MatchAny(any=memorial_ids)` через `query_filter` → нативная фильтрация
- Создан payload index: `client.create_payload_index('memorial-memories', 'memorial_id', INTEGER)`
- Файл: `backend/app/services/ai_tasks.py`

**Верификация cross-memorial RAG (E2E тест):**
- Вопрос "Расскажи о детях" для Николая (только memorial_5): 3 результата
- Вопрос "Расскажи о детях" для Николая + семья [5,3,4,10,20,21]: 30 результатов из всей семьи
- Вопрос "Расскажи о жене Людмиле" для [5,10]: 6 результатов из обоих мемориалов — работает!

**Состояние БД:**
- 10 мемориалов (ID: 3-10, 20, 21), 138 воспоминаний, 168 embeddings (30 призрачных, фильтруются)
- Все 10 мемориалов покрыты embeddings: 100%
- 36 семейных связей корректно отображают 2 семьи с пересечением через Людмилу (ID=10)

**Изменённые файлы:**
- `backend/app/api/family.py` — PARENT вместо CHILD в build_tree
- `backend/app/services/ai_tasks.py` — нативный фильтр Qdrant с MatchAny
- `frontend/src/components/FamilyTree.jsx` — loadAvailableMemorials + select вместо input

**Осталось сделать:**
- Запустить backend + frontend для визуальной проверки дерева
- Замена ELEVENLABS_API_KEY в .env на рабочий ключ (401 ошибка)

## [2026-03-11] Viral Share Button в MemoryList

**Статус:** завершено

**Что делали:** Встроили вирусную механику шеринга в компонент MemoryList и улучшили ContributePage.

**Изменённые файлы:**
- `frontend/src/components/MemoryList.jsx` — добавлен prop `memorialName`, кнопка "Пригласить друга", SharePanel с URL-копированием и Web Share API
- `frontend/src/components/MemoryList.css` — стили для `.memory-header-actions`, `.btn-share`, `.share-panel`, `.share-url-row`, `.btn-copy`, `.share-message-section`
- `frontend/src/pages/MemorialDetail.jsx` — передаётся `memorialName={memorial.name}` в MemoryList
- `frontend/src/pages/ContributePage.jsx` — тёплый текст в шапке, подсказка перед кнопкой записи, кнопка "Поделиться дальше" после сохранения с вирусной петлёй
- `frontend/src/pages/ContributePage.css` — стили для `.save-success-hint`, `.save-success-actions`, `.btn-viral-share`, `.record-hint`

## [2026-03-10] Подготовка демо для инвесторов

**Статус:** завершено

**DB засеяна:** 10 мемориалов + 141+ воспоминание + портреты + cover_photo_id для всех

## [2026-03-08] Улучшение читаемости семейного дерева
**Статус:** завершено
**Изменения:**
- FamilyTree.jsx: `renderTreeNode(node, level, relationLabel)` — новый параметр; словарь `RELATION_LABELS`; бейджи над именем в каждой карточке
- FamilyTree.css: `.node-relation-badge` (child=синий, spouse=розовый, root=серо-лиловый)

## [2026-03-08] Family Memory Synchronization — Layer 1 + Layer 2

**Статус:** завершено

**Layer 1 (real-time Cross-Memorial RAG):**
- `backend/app/schemas.py` — поле `include_family_memories: bool = False` в `AvatarChatRequest`
- `backend/app/services/ai_tasks.py` — `search_similar_memories()` принимает `memorial_ids: List[int]`
- `backend/app/api/ai.py` — family lookup + контекстные метки + family system prompt

**Layer 2 (Memory Sync Agent):**
- `backend/app/services/ai_tasks.py` — `sync_family_memories()`
- `backend/app/api/ai.py` — endpoint `POST /ai/family/sync-memories/{id}?dry_run=true`
- `frontend/src/components/AvatarChat.jsx` — кнопка "🔄 Синхр. с семьёй"

## [2026-03-07] Фикс чата с аватаром — Qdrant Cloud недоступен

**Статус:** завершено

**Решение:** Переключились на локальный файловый режим Qdrant.
Позже переключились обратно на Cloud (us-east-1-1): QDRANT_URL задан в .env

## 2026-04-19 — /run-tests + Stripe интеграция
**Статус:** завершено
**Что делали:** 
- Запустили pytest: 125/125 ✅
- E2E: SKIPPED — Playwright browsers не установлены (`npx playwright install` не запускался)
- Нашли баг: в memorial.spec.js:170 orphan-код вне test() — пофикшен, добавлен заголовок "13.7 Мобайл: карточки мемориалов не выходят за ширину 375px"
- Добавлены Pro + Lifetime Pro на лендинг (landing/index.html)
- Stripe интеграция: billing.py роутер, 4 endpoint'а, config.py с STRIPE_* переменными
**Изменённые файлы:** e2e/tests/memorial.spec.js, docs/TEST_PLAN.md, backend/app/api/billing.py, backend/app/config.py, backend/requirements.txt
**Осталось сделать:** npx playwright install chromium; заполнить STRIPE_* в .env и подключить webhook в Stripe Dashboard
