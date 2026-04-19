# Access Levels & Roles — Memorial MVP

> Версия: 2026-04-19. Stripe-интеграция — следующий шаг (см. раздел «Stripe»).

---

## 1. Роли на мемориале (MemorialAccess)

Роли определяют **что пользователь может делать с конкретным мемориалом**.
Хранятся в таблице `memorial_access` (поле `role`).

| Роль | Enum | Что может |
|------|------|-----------|
| **Owner** | `OWNER` | Полный контроль: редактирование, удаление, управление доступом (выдача ролей Editor/Viewer), загрузка медиа, управление приглашениями, настройка голоса |
| **Editor** | `EDITOR` | Добавление/редактирование воспоминаний и медиа, чат с аватаром. Не может менять настройки мемориала или выдавать доступ |
| **Viewer** | `VIEWER` | Только просмотр: медиа, воспоминания, чат с аватаром. Не может ничего добавлять |

**Как назначаются роли:**
- `OWNER` — создаётся автоматически при создании мемориала (`POST /memorials/`)
- `EDITOR` / `VIEWER` — Owner выдаёт через `POST /memorials/{id}/access/grant`
- Без регистрации — через invite-токен (`/contribute/:token`), разрешения задаются в `MemorialInvite.permissions`

**Приоритет ролей:** `VIEWER < EDITOR < OWNER`

---

## 2. Тарифные планы (SubscriptionPlan)

Планы определяют **сколько ресурсов** пользователь может использовать.
Хранятся в `users.subscription_plan`.

### Таблица лимитов

| Фича | Free ($0) | Plus ($7/мес · $59/год) | Pro ($15/мес · $120/год) | Lifetime ($99) | Lifetime Pro ($249) |
|------|-----------|-------------------------|--------------------------|----------------|---------------------|
| Мемориалов (owned) | 1 | 10 (+add-ons) | 10 (+add-ons) | 1 (залочен) | 1 (залочен) |
| Чат (msg/месяц) | 15 | 200 | 500 | 200 (только свой) | 200 (только свой) |
| TTS / голос аватара | Нет | Да | Да | Да | Да |
| Анимация фото | 0/мес | 5/мес | 15/мес | 5/мес | 15/мес |
| Family RAG | Нет | Да | Да | Нет | Нет |
| Live Avatar | Нет | Нет | 5 сессий/мес | Нет | Пул 100 сессий |
| Extra memorial slots | Нет | Да | Да | Нет | Нет |
| Хранилище | 500 MB | 5 GB | 15 GB | 5 GB | 10 GB |
| Срок действия | Бессрочно | До `plan_expires_at` → Free | До `plan_expires_at` → Free | Бессрочно | Бессрочно |

### Детали поведения планов

**Free:**
- Может иметь 1 мемориал (OWNER)
- Может быть EDITOR/VIEWER на чужих мемориалах без ограничений (роль ≠ тариф)
- Чат без голоса, 15 сообщений/месяц
- Нет анимации, нет TTS, нет Family RAG, нет Live Avatar

**Plus:**
- До 10 собственных мемориалов + add-on слоты
- TTS, анимация (5/мес), Family RAG
- Без Live Avatar (только Pro и выше)
- При истечении `plan_expires_at` автоматически падает на Free

**Pro:**
- До 10 собственных мемориалов + add-on слоты
- Всё что в Plus + 15 анимаций/мес + 5 live-сессий/мес
- Live-сессии дополнительно доступны через add-on паки
- При истечении `plan_expires_at` автоматически падает на Free

**Lifetime:**
- 1 конкретный мемориал (`users.lifetime_memorial_id`), залочен навсегда
- TTS и анимация доступны только для этого мемориала
- Без Family RAG, без Live Avatar
- Ориентирован на QR-коды на памятниках

**Lifetime Pro:**
- 1 конкретный мемориал, залочен навсегда
- Всё что Lifetime + Live Avatar из предоплаченного пула (`users.live_sessions_remaining`)
- Пул никогда не обнуляется, убывает при каждой сессии
- Можно докупить дополнительные сессии в пул

---

## 3. Демо-аккаунты

Демо-аккаунты (флаг `users.is_demo = true`) предназначены для демонстрации функционала всем пользователям.

**Правила для демо-аккаунтов:**
- Все биллинговые проверки **пропускаются** (нет лимитов чата, анимации, TTS, мемориалов)
- Семейный граф, TTS, анимация — всё доступно без ограничений
- Используются для seed-данных (43 мемориала Australian families)
- Текущие демо-юзеры: `en-demo@memorial.local` (id=1), `demo@memorial.app`

**Как работает доступ к демо-данным:**
- `INVESTOR_DEMO_MODE=true` → любой авторизованный пользователь видит все мемориалы как Owner
- `GLOBAL_ADMIN_EMAILS` → конкретные email имеют owner-доступ ко всем мемориалам
- Публичные мемориалы (`is_public=true`) → видны всем без авторизации

---

## 4. Матрица: Роль × Тариф

Роль и тариф — **независимые измерения**:
- Роль определяет доступ к конкретному мемориалу
- Тариф определяет доступ к AI-фичам и лимиты

| Сценарий | Роль | Тариф | Что может |
|----------|------|-------|-----------|
| Новый пользователь | OWNER своего мемориала | Free | 1 мемориал, чат без TTS, 15 msg/мес |
| Родственник по invite | EDITOR (через invite) | — (не авторизован) | Добавляет воспоминания, чат |
| Платный пользователь | OWNER нескольких | Plus | 10 мемориалов, TTS, анимация, Family RAG |
| Активный пользователь | OWNER нескольких | Pro | 10 мемориалов, TTS, 15 анимаций, 5 live-сессий/мес |
| QR на памятнике | OWNER одного | Lifetime | 1 мемориал навсегда, TTS, анимация |
| QR + live-видео | OWNER одного | Lifetime Pro | 1 мемориал + пул 100 live-сессий навсегда |
| Демо-пользователь | OWNER (is_demo=true) | Без лимитов | Все фичи открыты |

---

## 5. Endpoints с гейтингом

| Endpoint | Проверка роли | Проверка тарифа |
|----------|---------------|-----------------|
| `POST /memorials/` | — | `check_memorial_limit` |
| `POST /ai/avatar/chat` | VIEWER+ | `check_chat_quota` + `check_tts_access` + `check_family_rag_access` |
| `POST /ai/photo/animate` | EDITOR+ | `check_animation_quota` |
| `POST /ai/voice/upload` | OWNER | `check_tts_access` |
| `POST /ai/avatar/live` | VIEWER+ | `check_live_session_quota` |
| `POST /memorials/{id}/access/grant` | OWNER | — |
| `DELETE /memorials/{id}` | OWNER | — |

**HTTP коды ошибок:**
- `402 Payment Required` — превышена квота или фича недоступна на тарифе
- `401 Unauthorized` — не авторизован
- `403 Forbidden` — недостаточно прав на мемориале

---

## 6. Stripe-интеграция (следующий шаг)

Stripe будет управлять полями `users.subscription_plan` и `users.plan_expires_at`.

### Планируемые endpoints

```
POST /billing/checkout          → создаёт Stripe Checkout Session (redirect URL)
POST /billing/webhook           → Stripe webhook: обновляет plan/expires в БД
GET  /billing/usage             → текущие счётчики (chat_messages, animations) для UI
GET  /billing/portal            → Stripe Customer Portal (управление подпиской)
PATCH /admin/users/{id}/plan   → ручной апгрейд/даунгрейд (для тестирования)
```

### Логика вебхука

| Stripe Event | Действие в БД |
|--------------|---------------|
| `checkout.session.completed` (plus monthly) | `subscription_plan = "plus"`, `plan_expires_at = +1 month` |
| `checkout.session.completed` (plus annual) | `subscription_plan = "plus"`, `plan_expires_at = +1 year` |
| `checkout.session.completed` (pro monthly) | `subscription_plan = "pro"`, `plan_expires_at = +1 month` |
| `checkout.session.completed` (pro annual) | `subscription_plan = "pro"`, `plan_expires_at = +1 year` |
| `checkout.session.completed` (lifetime) | `subscription_plan = "lifetime"`, `lifetime_memorial_id = memorial_id` |
| `checkout.session.completed` (lifetime_pro) | `subscription_plan = "lifetime_pro"`, `lifetime_memorial_id = memorial_id`, `live_sessions_remaining = 100` |
| `checkout.session.completed` (live_session_pack) | `live_sessions_remaining += N` (add-on для Lifetime Pro) |
| `checkout.session.completed` (extra_memorial) | `extra_memorials += 1` (add-on для Plus/Pro) |
| `invoice.payment_succeeded` | Продление: обновляем `plan_expires_at` |
| `customer.subscription.deleted` | `subscription_plan = "free"`, `plan_expires_at = null` |

### Stripe Price IDs (заполнить перед интеграцией)

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PLUS_MONTHLY=price_...
STRIPE_PRICE_PLUS_ANNUAL=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_ANNUAL=price_...
STRIPE_PRICE_LIFETIME=price_...
STRIPE_PRICE_LIFETIME_PRO=price_...
STRIPE_PRICE_EXTRA_MEMORIAL=price_...      # add-on
STRIPE_PRICE_LIVE_SESSION_PACK_10=price_... # add-on: +10 live sessions
```

### Демо-аккаунты и Stripe

Демо-аккаунты (`is_demo=true`) **не проходят через Stripe** — их биллинг-лимиты всегда отключены независимо от тарифа в БД.

---

*Числовые лимиты — рабочая гипотеза MVP; подлежат A/B и пересмотру по метрикам.*
