# Handoff — Memorial MVP
> Обновлено: 2026-04-01 (session, late)

**Подробный журнал сессий — один файл:** [SESSION_LOG.md](SESSION_LOG.md) (новые блоки в начале файла). Здесь — кратко: фокус, последнее действие, next steps.

## Последнее действие (2026-04-01, session)
- **EN seed:** `seed_ensure_owner.py` — автосоздание `users.id=1` для цепочки `seed_english_all.py` (раньше требовался «запусти приложение»). **Исправлен pool leak** в `seed_english_cluster2.py` (один `with engine.connect()` на цикл рёбер). **Манифест:** `EXPECTED_EN_COUNT=43` — в список добавлены 5 имён из `seed_english.py` (Mary/Patricia/Arthur/Linda/Claire), иначе проверка в конце `seed_english_all.py` падала с «extra names».

## Последнее действие (2026-04-01, late)
- **Family tree — 4 семьи и split-рамка:** `FAMILY_TREE_SCOPE='kelly_anderson_four'`, колонки `A|center|B|C|D`, split-рамка для двойной фамилии по стороне связи (пример `Helen ... Anderson Kelly`) — детали в **[SESSION_LOG.md → 2026-04-01](SESSION_LOG.md)**.
- **Сборка:** `frontend npm run build` успешно.
- **Деплой:** попытка `vercel --prod --yes` упирается в невалидный токен (`vercel login` / новый `VERCEL_TOKEN`).

## Следующий шаг
- Выполнить `git push origin main` (если ещё не выполнен) и проверить автодеплой Vercel.
- Либо вручную: `vercel login` → `vercel --prod --yes`.

## Последнее действие (2026-04-01)
- **Family tree — коннекторы и читаемость:** таблица замечаний/решений (колонки Kelly/Anderson, marriageBarInGap, parent-child yH, вилка+mx, yFork над детьми, пунктир sibling) — **[SESSION_LOG.md → 2026-04-01](SESSION_LOG.md)**. В коде: увеличены вертикаль вилка→ребёнок (`forkMargin`) и жирность пунктира sibling/half_sibling в `familyTreeOrthogonalConnectors.js`. **Снимок состояния:** коммит `18a0f80`.

## Предыдущее действие (2026-03-31)
- **Family tree — сиблинги в один ряд:** исправление БД (`repair_expanded_family_rels.py`: снять ложный parent/child между Sarah↔Daniel и **George↔Helen**, SIBLING; `engine.echo=false` в скрипте), API — `_infer_sibling_pairs_from_shared_parents` в `family.py`, фронт — `stripSiblingConflictingParentEdges` + доработки поколений/коннекторов. Подробности и таблица — **[SESSION_LOG.md → 2026-03-31](SESSION_LOG.md)**.
- **Показ двух семей в UI:** `FAMILY_TREE_SCOPE` в `familyTreeKellyFilter.js` — `'kelly_anderson'` (Kelly + Anderson по последней фамилии, без Chang/Rossi), `'kelly'` только Kelly, `'full'` весь граф API.

## Предыдущее действие (2026-03-30)
- **Family tree — фаза 1 (только Kelly):** `frontend/src/utils/familyTreeKellyFilter.js` — `FAMILY_TREE_KELLY_ONLY`, фильтр узлов по фамилии Kelly (`surnameOf` === `Kelly`), рёбра только внутри подграфа; `root_id` — открытый мемориал если Kelly, иначе BFS от полного графа к ближайшему Kelly, иначе самый старый по `birth_year`. В `FamilyTree.jsx` дерево и раскладка считаются по `displayGraph`; блок «Connected families» скрыт в этой фазе. Баннер `family.kelly_only_banner` + стиль `.ft-kelly-only-banner`.
- **Family tree (поколения):** раскладка рядов через `computeLayoutDepthOldestTop` в `familyTreeGenerations.js` — сверху корни (без родителей в графе), ниже дети; не зависит от `root_id` / фокального мемориала (раньше `refineFullTreeGenerations` сдвигал этажи относительно открытой карточки). Подключено в `buildGenerationLayout` (`familyTreeGenerationLayout.js`).
- **Лендинг:** демо-видео в `#demo`, копирование `video` в `dist`, hero/QR-блоки без перекрытия лица/камня; на секции Physical memorial — декоративная табличка QR + подпись про иллюстрацию.
- **SPA:** источники чата в сворачиваемом блоке; timeline включает воспоминания без `event_date`; инвайты для **editor** + правильные URL contribute через `utils/inviteUrl.js`; при смене мемориала сброс вкладок и QR state.
- **Детали, тесты, что не сделано:** см. **[SESSION_LOG.md → 2026-03-30](SESSION_LOG.md)**.

## Дополнение 2026-03-29 — деплой Vercel: лендинг + `/app`
**Сделано в Cursor (нужна вторая пара глаз — см. чеклист в логе):** корень сайта = **`landing/index.html`**, React SPA = **`/app/`** (`vite` production `base` + `outDir dist/app` + копирование лендинга в `dist/`; `vercel.json` rewrites только для `/app`). Лендинг: ссылки на **`/app/login`**, **`/app/register`**; **`backend/.env.example`**: `FRONTEND_URL` / `PUBLIC_FRONTEND_URL` с суффиксом **`/app`** для прода. **Полный перечень файлов и чеклист для Claude Code:** [SESSION_LOG.md](SESSION_LOG.md) → запись **[2026-03-29]**.

## Что сейчас в фокусе
Вкладка мемориала **Family** — **семейное дерево** (`FamilyTree`). `FamilyNetwork` не в `MemorialDetail`, остаётся в коде для демо/API `network-clusters`.

## Предыдущее действие (2026-03-28)
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

## Изменённые файлы
- **Актуальная сессия (2026-03-30):** перечень путей — в [SESSION_LOG.md](SESSION_LOG.md) → блок **2026-03-30**.
- **Ранее (2026-03-28 и др.):** Family — `MemorialDetail` / `FamilyTree`, `FamilyNetwork` в коде без переключателя в UI; см. также **Предыдущее действие** выше.

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
