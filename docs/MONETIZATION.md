# Монетизация Memorial — Вариант C (текущая реализация)

> Версия: 2026-04-15. Stripe-интеграция — следующий шаг после тестирования гейтов.

## Выбранная модель

**Гибрид: Freemium + годовая/месячная подписка + разовая покупка Lifetime.**

| Тариф | Цена | Назначение |
|-------|------|------------|
| **Free** | $0 | Воронка: 1 мемориал, текстовый чат (15 msg/мес), без голоса и анимации. |
| **Plus** | $7/мес · $59/год | Основной MRR: до 10 мемориалов, TTS, анимация, Family RAG. |
| **Lifetime** | $99 разово | Для QR-кодов на памятниках: полные AI-фичи для 1 мемориала навсегда. |

## Лимиты по тарифам (реализованы в `billing.py`)

| Фича | Free | Plus | Lifetime |
|------|------|------|----------|
| Мемориалов | 1 | 10 | 1 (залочен) |
| Чат (msg/мес) | 15 | 200 | 200 (только свой мемориал) |
| TTS / голос | Нет | Да | Да |
| Анимация фото | 0 рендеров | 5/мес | 5/мес |
| Family RAG | Нет | До 10 мемориалов | Нет |
| Хранилище | 500 MB | 5 GB | 5 GB |

## Архитектура гейтинга

### Модели БД
- `users.subscription_plan` — `"free"` | `"plus"` | `"lifetime"` (default: `"free"`)
- `users.plan_expires_at` — дата истечения подписки Plus (NULL = нет expiry)
- `users.lifetime_memorial_id` — ID мемориала для Lifetime (NULL если не Lifetime)
- `user_usage` — счётчики чата и анимации по периодам (`user_id`, `period` = "YYYY-MM")

### Сервис
`backend/app/services/billing.py` — все проверки квот:
- `check_memorial_limit(user, db)` — перед созданием мемориала
- `check_chat_quota(user, memorial_id, db)` — перед чатом
- `check_animation_quota(user, db)` — перед анимацией
- `check_tts_access(user)` — перед TTS и загрузкой голоса
- `check_family_rag_access(user)` — перед family RAG
- `increment_chat_usage / increment_animation_usage` — после успешного вызова

### Применённые гейты
| Endpoint | Гейт |
|----------|------|
| `POST /memorials/` | `check_memorial_limit` |
| `POST /ai/avatar/chat` | `check_chat_quota` + `check_family_rag_access` + `check_tts_access` |
| `POST /ai/photo/animate` | `check_animation_quota` (требует auth) |
| `POST /ai/voice/upload` | `check_tts_access` (требует auth) |

## Следующие шаги

1. **Stripe Checkout** — `POST /billing/checkout` (создаёт Stripe Session)
2. **Stripe Webhook** — обновление `subscription_plan` / `plan_expires_at` в БД
3. **Billing UI** — страница `/app/pricing` со ссылкой на checkout
4. **Admin endpoint** — `PATCH /admin/users/{id}/plan` для ручного апгрейда на тестирование
5. **Usage endpoint** — `GET /billing/usage` → возвращает счётчики для UI (чтобы показывать "15/15 сообщений")

## HTTP коды ошибок

- `402 Payment Required` — превышена квота или фича недоступна на тарифе
- `401 Unauthorized` — не авторизован (для фич, требующих авторизации)

---

*Числовые лимиты — рабочая гипотеза MVP; подлежат A/B и пересмотру по метрикам.*
