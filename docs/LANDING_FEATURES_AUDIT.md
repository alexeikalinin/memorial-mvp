# Сверка лендинга с кодом (Memorial MVP)

Обновлено: 2026-03-30. Источник лендинга для деплоя: **`frontend/landing/index.html`** (копируется в `dist/index.html` при `npm run build`).

## Изображения

Сгенерированные ассеты лежат только в **`frontend/landing/images/`** (корневой `landing/images/` не дублируем) и копируются в **`dist/images/`** плагином Vite (`vite.config.js`).

| Файл | Назначение на странице |
|------|-------------------------|
| `hero-portrait.png` | Герой, портрет |
| `demo-poster.png` | Блок «Watch demo» (постер; видео `video/demo.mp4` по-прежнему нужно добавить отдельно) |
| `feat-chat.png` | Блок AI Avatar Chat |
| `feat-voice.png` | Voice cloning |
| `feat-timeline.png` | Life Timeline |
| `feat-tree.png` | Family Tree + фон финального CTA |
| `feat-headstone.png` | QR / physical memorial |
| `testi-1.png` … `testi-3.png` | Аватары отзывов (иллюстрации, не реальные клиенты) |

## Фичи: лендинг ↔ код

| На лендинге | В коде | Примечание |
|-------------|--------|------------|
| AI avatar chat (RAG) | `POST /api/v1/ai/avatar/chat`, `generate_rag_response` | Модель по умолчанию: `gpt-4o-mini` (`OPENAI_MODEL` в `config.py`). |
| Озвучка ElevenLabs | `generate_speech_elevenlabs`, клонирование голоса в `ai_tasks` | Требует ключи API. |
| Оживление фото | D-ID / HeyGen, `USE_HEYGEN`, `animate_photo` | Оба провайдера в коде. |
| Векторный поиск | Qdrant или Pinecone, `VECTOR_DB_PROVIDER` | Лендинг: «Qdrant / Pinecone». |
| Семейное дерево | `GET .../full-tree`, поколения в `FamilyTree.jsx` | Есть режим «поколения» и педигри. |
| Hidden Connections | `GET .../hidden-connections` | Есть. |
| Семейный RAG | `include_family_memories` в чате | В API есть; лимиты по тарифам — **roadmap** (`docs/MONETIZATION.md`). |
| Инвайты без аккаунта | `ContributePage`, `invites` API | Есть. |
| Google login | OAuth callback, `GOOGLE_CLIENT_ID` | Есть при настройке env. |
| Цены $0 / $14 / $149, лимиты чата | **Нет Stripe / биллинга в репозитории** | На лендинге указано, что **оплата ещё не включена**; цифры совпадают с **черновиком** `MONETIZATION.md`, не с enforcement в коде. |
| «14-day trial» | Не реализовано | **Убрано** с лендинга. |

## Что в приложении есть, но на лендинге кратко

- Биография / агенты: `POST .../ai/biography`, quality — в API, на лендинге не выделено.
- Экспорт данных: заявлен в FAQ в общих чертах; полнота зависит от реализации эндпоинтов экспорта.

## Рекомендации

1. Добавить реальный **`frontend/landing/video/demo.mp4`** (или встроить YouTube) — постер уже локальный.
2. После появления биллинга — обновить блок Pricing и FAQ под фактические условия и Stripe.
