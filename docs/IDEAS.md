# Ideas & Backlog — Memorial MVP

> Единый список идей, незаконченных фич и roadmap-пунктов.
> Обновляется вручную или через скилл `/idea`.
> Статусы: `idea` → `planned` → `in-progress` → `done` | `dropped`

> **Полный структурированный roadmap MVP → Product:** [`docs/ROADMAP.md`](ROADMAP.md)

---

## Продуктовые идеи (новые фичи)

### Личное обращение в связях (nickname_for_visitor)
**Статус:** `planned`
**Откуда:** обсуждение 2026-04-29 — «дедушка называл меня Лёшик»
**Описание:** При создании/редактировании связи (мама, дедушка, друг…) добавить опциональное поле **«Как он(а) тебя называл(а)?»** — например «Лёшик», «солнышко», «внучок». Это поле сохраняется в `notes` или новое поле `nickname_for_visitor` в `FamilyRelationship`.

**Как использовать в чате:** при построении system_prompt для аватара чата — находить связь current_user → memorial, и если `nickname_for_visitor` задан, добавлять в промпт: *"The person you're speaking with is your grandson. You used to call him 'Lyoshik'."* Это делает разговор намного правдоподобнее.

**Что нужно реализовать:**
1. `FamilyRelationship` → новая колонка `nickname_for_visitor VARCHAR(100) NULL` (или переиспользовать `notes` до поры)
2. UI в `FamilyTree.jsx` → поле в форме создания/редактирования связи (подпись: «Как он(а) вас называл(а)? — необязательно»)
3. API: схемы `FamilyRelationshipCreate/Update` + endpoint PATCH `/family/{id}`
4. В `ai.py` → `avatar_chat`: при поиске связи current_user ↔ memorial, если `nickname_for_visitor` есть — вставить в system_prompt
**Зависит от:** авторизованный пользователь должен иметь связь с мемориалом (т.е. его собственный мемориал должен быть в дереве)

---

### Pedigree layout для семейного дерева
**Статус:** `idea`
**Откуда:** упрощение UI 2026-04-14
**Описание:** Классический "Pedigree" режим отображения дерева (ancestors-only, строго влево/вправо). Сейчас вкладка скрыта — базовый код уже есть (`relatives-tree` lib), но UX сырой. Вернуть когда: есть дизайн, понятно чем отличается от Generation layout для пользователя.

---



### Memory Graph View
**Статус:** `idea`
**Откуда:** обсуждение с Obsidian 2026-04-13
**Описание:** Визуализация всех воспоминаний и связей между людьми в виде интерактивного графа — как Obsidian Graph View, но для семейной истории. Каждый узел — мемориал или воспоминание, рёбра — родственные связи и общие события.
**Технический базис:** уже есть `FamilyRelationship` edges, `network-clusters` API, `FamilyNetwork.jsx` (SVG). Нужно: расширить на memories как узлы, добавить фильтры по тегам/периодам.
**Ценность:** уникальный дифференциатор; подтверждён спросом (Obsidian — 1M+ пользователей именно за этот паттерн).

---

### Obsidian как инструмент команды (не для пользователей)
**Статус:** `idea`
**Откуда:** обсуждение 2026-04-13
**Описание:** Открыть репозиторий как Obsidian vault — получить Graph View всей документации, Canvas для архитектурных диаграмм, поиск по всем md-файлам. Не меняет код, не ломает ничего.
**Как подключить:** просто открыть папку `/memorial-mvp` в Obsidian (File → Open vault → папка репо).
**Что даёт:** граф связей между `HANDOFF.md`, `SESSION_LOG.md`, `docs/`, `CLAUDE.md`; Canvas для диаграмм; шаблоны для новых записей.
**Риски:** ноль. Obsidian создаёт только папку `.obsidian/` (добавить в `.gitignore`).

---

### Stripe биллинг (монетизация)
**Статус:** `planned`
**Откуда:** `docs/MONETIZATION.md`
**Описание:** Реализовать тарифы Free / Plus / Lifetime с Stripe. Черновик лимитов уже есть в `MONETIZATION.md`.
**Нужно:** Stripe Customer + Subscription + одноразовый PaymentIntent; middleware FastAPI для проверки тарифа перед чатом/анимацией/TTS; UI страницы подписки.

---

### Enforcement лимитов по тарифам в API
**Статус:** `planned`
**Откуда:** `docs/MONETIZATION.md`, `docs/LANDING_FEATURES_AUDIT.md`
**Описание:** На лендинге показаны лимиты чата/TTS/рендеров, но в коде они не enforced. Нужен FastAPI dependency/middleware: проверка тарифа → счётчик → 402 если превышен.
**Зависит от:** Stripe биллинг.

---

### 14-day trial
**Статус:** `idea`
**Откуда:** `docs/LANDING_FEATURES_AUDIT.md` — было на лендинге, убрано как нереализованное
**Описание:** Пробный период для Plus — автоматически, без карты или с заморозкой.

---

### Export данных мемориала
**Статус:** `idea`
**Откуда:** FAQ лендинга упоминает экспорт; в коде неполно
**Описание:** Экспорт мемориала в ZIP: все фото/видео + воспоминания в JSON или PDF. Важно для «не боюсь потерять данные» нарратива.

---

### Biography Agent в UI
**Статус:** `idea`
**Откуда:** `docs/LANDING_FEATURES_AUDIT.md` — есть в API (`POST /api/v1/ai/biography`), не показан на лендинге и не встроен в UX мемориала
**Описание:** Кнопка «Сгенерировать биографию» на странице мемориала → AI синтезирует биографический текст из всех воспоминаний → можно редактировать и опубликовать.

---

### Memory Quality Agent в UI
**Статус:** `idea`
**Откуда:** есть `POST /api/v1/ai/memory/quality`, нет UI
**Описание:** После добавления воспоминания — подсказка AI: «это воспоминание расплывчатое, уточните дату / добавьте деталей». Inline в `MemoryList`.

---

### Реальное demo-видео (живой screen capture)
**Статус:** `idea`
**Откуда:** `docs/LANDING_FEATURES_AUDIT.md`, `frontend/landing/video/SCREEN_RECORDING.md`
**Описание:** Заменить сгенерированный `demo.mp4` живой записью экрана по готовому скрипту `DEMO_VIDEO_SCRIPT.md`.

---

### Портреты Chang/Rossi (IDs 42-56)
**Статус:** `planned`
**Откуда:** `HANDOFF.md` → Незавершённые задачи
**Описание:** Добавить `cover_photo_id` для мемориалов Chang и Rossi в `seed_english_portraits.py`.

---

### Embeddings для Chang/Rossi воспоминаний
**Статус:** `planned`
**Откуда:** `HANDOFF.md` → Незавершённые задачи
**Описание:** Проверить и при необходимости пересоздать embeddings для воспоминаний новых кластеров. RAG-чат может не находить релевантный контекст.

---

### Семейный RAG в платных тарифах
**Статус:** `planned`
**Откуда:** `docs/LANDING_FEATURES_AUDIT.md` — «включён до N мемориалов, например 10»
**Описание:** `include_family_memories: true` сейчас доступен всем. Нужно ограничить Free-тарифом и включить только для Plus/Family.

---

### Provider field в модели Media
**Статус:** `idea`
**Откуда:** `backend/app/workers/worker.py:72` — `# TODO: Добавить поле provider в модель Media`
**Описание:** Хранить в БД провайдера анимации (D-ID / HeyGen) для каждого медиа-файла, чтобы знать как отзывать/пересоздавать.

---

### Публичный URL для анимации в dev без ngrok
**Статус:** `idea`
**Откуда:** `backend/app/workers/worker_simple.py:29` — `# TODO: Получить публичный URL изображения`
**Описание:** Нужен способ получать публичный URL для D-ID без настройки ngrok — например загрузка на временный S3 bucket или использование presigned URL.

---

## Технический долг

### Auth — убрать hardcode owner_id=1
**Статус:** `in-progress`
**Откуда:** `CLAUDE.md` — «No authentication yet — owner_id is hardcoded to 1»
**Описание:** JWT auth уже частично есть (`auth.py`), но `memorials.py` местами использует hardcode. Довести до конца.

### Vercel деплой — валидный токен
**Статус:** `planned`
**Откуда:** `HANDOFF.md` — `vercel login` / новый `VERCEL_TOKEN` после 2026-04-01
**Описание:** Обновить `VERCEL_TOKEN` в CI или залогиниться вручную.

### GOT-style family tree — финальная проверка
**Статус:** `planned`
**Откуда:** `HANDOFF.md` → Следующий шаг
**Описание:** Открыть EN-демо (Kelly → Family), проверить GOT-стиль и Anderson stubs в правильном поколении.

---

### Family Tree Editor: кликабельные коннекторы (удаление / смена типа связи)
**Статус:** `idea`
**Откуда:** обсуждение 2026-04-14
**Описание:** В edit mode — клик по линии связи между мемориалами открывает попап с двумя действиями: «Удалить связь» и «Изменить тип» (например parent → spouse). Сейчас управление связями только через список ниже дерева, что неудобно если связь выстроилась некорректно.
**Технический базис:** `orthoConnectorLines` содержат координаты линий, но не ссылку на edge. Нужно: (1) добавить `edgeKey: "sourceId|targetId"` в каждую линию внутри `buildOrthogonalConnectors`, (2) добавить прозрачный fat-stroke (12px) для hit area, (3) попап с DELETE + тип-селектор → `familyAPI.deleteRelationship` / `familyAPI.updateRelationship`.
**Ценность:** критично для UX — пользователь видит неверную связь прямо на графе и хочет исправить там же, не листая список.

---

---

## 🔴 Launch Blockers — незавершённые (аудит 2026-05-02)

### AUTH-2: Email верификация при регистрации
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** После `POST /auth/register` — письмо с токеном верификации. До подтверждения — нельзя создавать мемориалы и платить. Нужно: email-провайдер (Resend / SendGrid), шаблон письма, `GET /auth/verify/{token}`.

---

### AUTH-3: Сброс пароля
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** `POST /auth/password-reset` (запрос) + `POST /auth/password-reset/confirm` (токен из письма). Email-провайдер тот же что AUTH-2. UI форма.

---

### AUTH-4: OAuth Google — end-to-end на проде
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Код callback есть, но на проде не тестировался. Проверить `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`, полный флоу.

---

### BILLING-1: Stripe Checkout — end-to-end
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Код `POST /billing/checkout` есть. Проверить: Session → редирект → webhook `checkout.session.completed` → `subscription_plan` обновился в БД. Тестировать все 5 планов.

---

### BILLING-2: Stripe Webhooks — полное покрытие
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Обработать: `invoice.payment_succeeded` → продление `plan_expires_at`, `customer.subscription.deleted` → даунгрейд до Free, add-on события (extra_memorial, live_session_pack).

---

### BILLING-3: Billing UI — страница подписки
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Страница `/app/billing`: текущий план + дата продления, кнопка апгрейда → Stripe Checkout, использование (чаты, анимации) через `GET /billing/usage`, Stripe Customer Portal для отмены.

---

### SECURITY-1: Rate limiting
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** `slowapi` (FastAPI) или nginx. Login: 5 req/мин на IP; Chat: 60 req/мин на user; Animate: 10 req/мин на user; все публичные: 100 req/мин на IP.

---

### SECURITY-2: Валидация файлов по MIME + лимиты по тарифу
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Проверять MIME по содержимому файла (не расширению). Лимиты размера: Free 500MB, Plus 5GB, Pro 15GB. `media_service.py` сейчас проверяет ограниченно.

---

### MONITORING-1: Sentry (backend + frontend)
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** `sentry-sdk` в FastAPI, `@sentry/react` в Vite. Алерты на 5xx и деградацию AI-сервисов. Без мониторинга о падениях узнаём от пользователей.

---

### INFRA-1: CI/CD GitHub Actions
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** При PR → pytest + Playwright. При merge в main → деплой backend (Railway/Fly.io) + frontend (Vercel). Обновить `VERCEL_TOKEN` (истёк после 2026-04-01).

---

## 🟡 Core UX — незавершённые

### UX-1: Онбординг нового пользователя
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Checklist или guided tour после регистрации: создай мемориал → загрузи фото → добавь воспоминание → попробуй чат. Метрика: % дошедших до первого воспоминания.

---

### UX-2: Инвайт по email
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Сейчас `POST /invites/` создаёт токен, но письмо не шлётся. Нужно автоматически отправлять email с ссылкой `/contribute/:token`. Email-провайдер тот же что AUTH-2/3.

---

### UX-3: Email-уведомление о новых воспоминаниях
**Статус:** `planned`
**Откуда:** ROADMAP.md, аудит 2026-05-02
**Описание:** Когда родственник добавил воспоминание через инвайт — email владельцу мемориала. «Иван добавил воспоминание о Сергее Иванове».

---

## Идеи из обсуждений (лог)

| Дата | Идея | Статус |
|------|------|--------|
| 2026-04-13 | Memory Graph View (Obsidian-стиль) | `idea` |
| 2026-04-13 | Obsidian как vault для документации проекта | `idea` |
| 2026-04-14 | Family Tree Editor: кликабельные коннекторы (удалить / сменить тип связи) | `idea` |
| 2026-05-02 | AUTH-2/3: Email верификация + сброс пароля (Resend/SendGrid) | `planned` |
| 2026-05-02 | BILLING-1/2/3: Stripe Checkout e2e + webhooks + billing UI | `planned` |
| 2026-05-02 | SECURITY-1/2: Rate limiting + MIME-валидация файлов | `planned` |
| 2026-05-02 | MONITORING-1: Sentry backend + frontend | `planned` |
| 2026-05-02 | INFRA-1: CI/CD GitHub Actions + обновить VERCEL_TOKEN | `planned` |
| 2026-05-02 | UX-1/2/3: Онбординг + инвайт по email + уведомления | `planned` |

---

*Обновляй этот файл через `/idea "название идеи"` или `/defer "идея"` (для отложенных). Статусы: `idea` → `planned` → `in-progress` → `done` | `dropped`.*
