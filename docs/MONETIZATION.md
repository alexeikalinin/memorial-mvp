# Монетизация Memorial — Вариант C (текущая реализация)

> Версия: 2026-04-19. Stripe-интеграция — следующий шаг после тестирования гейтов.
> Подробная матрица ролей × тарифов + Stripe-план: **[ACCESS_LEVELS.md](ACCESS_LEVELS.md)**

## Выбранная модель

**Гибрид: Freemium + подписка (Plus/Pro) + разовая покупка Lifetime.**

| Тариф | Цена | Назначение |
|-------|------|------------|
| **Free** | $0 | Воронка: 1 мемориал, текстовый чат (15 msg/мес), без голоса и анимации. |
| **Plus** | $7/мес · $59/год | Основной MRR: до 10 мемориалов, TTS, анимация, Family RAG. Без Live Avatar. |
| **Pro** | $15/мес · $120/год | Топ-подписка: все фичи Plus + 5 live-сессий/мес + 15 анимаций. |
| **Lifetime** | $99 разово | Для QR-кодов на памятниках: полные AI-фичи для 1 мемориала навсегда. |
| **Lifetime Pro** | $249 разово | То же, что Lifetime + пул из 100 live-сессий (никогда не обнуляются). |

## Add-ons (хранятся на User)

| Add-on | Доступен для | Описание |
|--------|-------------|----------|
| `extra_memorials` | Plus, Pro | Дополнительные слоты мемориалов сверх лимита плана |
| `live_sessions_remaining` | Lifetime Pro | Предоплаченный пул live-сессий; убывает при каждой сессии |

## Лимиты по тарифам (реализованы в `billing.py`)

| Фича | Free | Plus | Pro | Lifetime | Lifetime Pro |
|------|------|------|-----|----------|--------------|
| Мемориалов | 1 | 10 (+add-ons) | 10 (+add-ons) | 1 (залочен) | 1 (залочен) |
| Чат (msg/мес) | 15 | 200 | 500 | 200 (только свой) | 200 (только свой) |
| TTS / голос | Нет | Да | Да | Да | Да |
| Анимация фото | 0 | 5/мес | 15/мес | 5/мес | 15/мес |
| Family RAG | Нет | Да | Да | Нет | Нет |
| Live Avatar | Нет | Нет | 5/мес | Нет | Пул 100 сессий |
| Extra memorials | Нет | Да | Да | Нет | Нет |
| Хранилище | 500 MB | 5 GB | 15 GB | 5 GB | 10 GB |

## Архитектура гейтинга

### Модели БД
- `users.subscription_plan` — `"free"` | `"plus"` | `"pro"` | `"lifetime"` | `"lifetime_pro"` (default: `"free"`)
- `users.plan_expires_at` — дата истечения подписки Plus/Pro (NULL = нет expiry)
- `users.lifetime_memorial_id` — ID мемориала для Lifetime/Lifetime Pro (NULL если не Lifetime)
- `users.extra_memorials` — купленные дополнительные слоты мемориалов (Plus/Pro only)
- `users.live_sessions_remaining` — предоплаченный пул сессий для Lifetime Pro
- `user_usage` — счётчики чата, анимации и live-сессий по периодам (`user_id`, `period` = "YYYY-MM")

### Сервис
`backend/app/services/billing.py` — все проверки квот:
- `check_memorial_limit(user, db)` — перед созданием мемориала (учитывает `extra_memorials`)
- `check_chat_quota(user, memorial_id, db)` — перед чатом
- `check_animation_quota(user, db)` — перед анимацией
- `check_tts_access(user)` — перед TTS и загрузкой голоса
- `check_family_rag_access(user)` — перед family RAG
- `check_live_session_quota(user, db)` — перед live-сессией аватара
- `increment_chat_usage / increment_animation_usage / increment_live_session_usage` — после успешного вызова

### Применённые гейты
| Endpoint | Гейт |
|----------|------|
| `POST /memorials/` | `check_memorial_limit` |
| `POST /ai/avatar/chat` | `check_chat_quota` + `check_family_rag_access` + `check_tts_access` |
| `POST /ai/photo/animate` | `check_animation_quota` |
| `POST /ai/voice/upload` | `check_tts_access` |
| `POST /ai/avatar/live` | `check_live_session_quota` |

## Следующие шаги

1. **Stripe Checkout** — `POST /billing/checkout` (создаёт Stripe Session для Plus/Pro/Lifetime/Lifetime Pro)
2. **Stripe Webhook** — обновление `subscription_plan` / `plan_expires_at` / `live_sessions_remaining` в БД
3. **Billing UI** — страница `/app/pricing` со ссылкой на checkout
4. **Admin endpoint** — `PATCH /admin/users/{id}/plan` для ручного апгрейда на тестирование
5. **Usage endpoint** — `GET /billing/usage` → возвращает счётчики для UI
6. **Live Avatar endpoint** — `POST /ai/avatar/live` с вызовом `check_live_session_quota`

## HTTP коды ошибок

- `402 Payment Required` — превышена квота или фича недоступна на тарифе
- `401 Unauthorized` — не авторизован (для фич, требующих авторизации)

---

*Числовые лимиты — рабочая гипотеза MVP; подлежат A/B и пересмотру по метрикам.*
