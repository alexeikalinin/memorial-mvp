# Handoff — Memorial MVP
> Обновлено: 2026-03-29 (session)

## Дополнение 2026-03-29 — деплой Vercel: лендинг + `/app`
**Сделано в Cursor (нужна вторая пара глаз — см. чеклист в логе):** корень сайта = **`landing/index.html`**, React SPA = **`/app/`** (`vite` production `base` + `outDir dist/app` + копирование лендинга в `dist/`; `vercel.json` rewrites только для `/app`). Лендинг: ссылки на **`/app/login`**, **`/app/register`**; **`backend/.env.example`**: `FRONTEND_URL` / `PUBLIC_FRONTEND_URL` с суффиксом **`/app`** для прода. **Полный перечень файлов и чеклист для Claude Code:** [SESSION_LOG.md](SESSION_LOG.md) → запись **[2026-03-29] Vercel: лендинг на `/`...**.

## Что сейчас делается
Вкладка мемориала **Family** по умолчанию показывает только **семейное дерево** (relatives-tree). Вид **All Families** / `FamilyNetwork` убран из `MemorialDetail` — кластерный обзор остаётся в коде (`FamilyNetwork.jsx` + API `network-clusters`) для демо/отладки при необходимости.

## Последнее действие (2026-03-28)
- **EN демо = 35 мемориалов в репозитории:** добавлены `backend/en_memorials_manifest.py` (канонический frozenset имён), `backend/seed_english_all.py` (последовательный запуск трёх сидов + проверка COUNT/имён), `tests/test_en_memorials_manifest.py`. Обновлены docstring’и `seed_english*.py`, в `CLAUDE.md` — команда `seed_english_all.py`.
- `Home.jsx`: `memorialsAPI.list(lang)` — список на главной фильтруется по `Memorial.language`, иначе смешивались RU+EN и число карточек не совпадало с «английским» набором из сидов.
- `MemorialDetail`: удалён `FamilyViewToggle`, рендерится только `<FamilyTree memorialId={id} />`; убраны стили `.family-view-*` из `MemorialDetail.css`.
- `FamilyTree`: кнопки **«Показать всё дерево»** (fit холста в viewport) и **«К этому человеку»** (центр на открытом мемориале, `root_id`); зум наружу до `MIN_SCALE=0.05`; подсказка `tree_controls`.
- Локали `en.js` / `ru.js`: `family.fit_whole_tree`, `family.center_on_person`.

## Предыдущее (Family Network)
- Добавлен backend endpoint `GET /api/v1/family/memorials/{id}/network-clusters` (`family.py`)
- Добавлены Pydantic схемы `NetworkClustersResponse`, `NetworkCluster`, `NetworkBridge` (`schemas.py`)
- Создан `frontend/src/components/FamilyNetwork.jsx` — SVG-визуализация с островками кластеров и пунктирными мостами
- Создан `frontend/src/components/FamilyNetwork.css`
- В `MemorialDetail.jsx` добавлен переключатель Tree / Network (компонент `FamilyViewToggle`)
- Добавлен `familyAPI.getNetworkClusters()` в `client.js`
- Исправлен DB: relationship_type нормализованы в UPPERCASE (SQLAlchemy читает по именам enum)
- Добавлены пропущенные структурные связи для IDs 48-56 (Chang+Rossi семьи не были соединены)

## Следующий шаг
- Добавить портреты для Chang/Rossi (IDs 42-56) в `seed_english_portraits.py` и запустить
- Проверить Family Tree: fit / center / зум на большом графе
- Проверить embeddings для Chang/Rossi воспоминаний

## Незавершённые задачи
- Портреты для IDs 42-56 (Chang/Rossi) — нет cover_photo_id
- Embeddings для Chang/Rossi воспоминаний: проверить завершился ли фоновый процесс
- Тест RAG-чата на нескольких мемориалах нового кластера

## Изменённые файлы (текущая сессия)
- `frontend/src/pages/MemorialDetail.jsx` — только `FamilyTree`, без переключателя
- `frontend/src/pages/MemorialDetail.css` — удалены стили переключателя
- `frontend/src/components/FamilyTree.jsx` — fit/center, зум 0.05–3
- `frontend/src/components/FamilyTree.css` — `.tree-view-controls`, `.btn-tree-view`, `.tree-controls-hint`
- `frontend/src/locales/en.js`, `ru.js` — строки fit/center
- Ранее: `backend/app/api/family.py` `/network-clusters`, `FamilyNetwork.jsx`, `client.js`, DB structural links и т.д.

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Критический контекст
- **Vercel (после 2026-03-29):** лендинг на `/`, приложение на **`/app`**; в проде **`FRONTEND_URL` / `PUBLIC_FRONTEND_URL`** на бэкенде — с **`/app`**; детали — `SESSION_LOG.md` [2026-03-29].
- SQLAlchemy `Enum(RelationshipType)` читает по **именам** (PARENT, CHILD...), DB должна хранить UPPERCASE
- Cluster endpoint: `GET /api/v1/family/memorials/{id}/network-clusters`
- 4 кластера: [0] Морозов (21), [1] Kelly/Anderson (20), [2] Chang (9), [3] Rossi (6)
- 8 cross-cluster bridges с custom_label из DB
- Family tab: только `FamilyTree` (без `FamilyViewToggle`)
- Docs index: ENVIRONMENT.md, docs/MONETIZATION.md, docs/TEST_PLAN.md, INVESTOR_DEMO_PLAN.md
