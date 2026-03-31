# Session Log — Memorial MVP

> **Где хранится:** этот файл в корне репозитория — рабочая копия для Cursor/IDE. Дублирующий экземпляр: `~/.claude/projects/-Users-alexei-kalinin-Documents-VibeCoding-memorial-mvp/memory/session_log.md`. Новые записи добавлять **в начало** (после этого блока).

## Как вести журнал (Claude Code / Cursor)

| Файл | Назначение |
|------|------------|
| **`SESSION_LOG.md`** (этот файл) | **Единый подробный журнал сессий:** что сделали, результат, решения, что не сделали / отложили. Новые блоки — **в начало**, после вводного абзаца. |
| **`HANDOFF.md`** | **Краткий handoff:** текущий фокус, последнее действие в 3–7 строк, следующий шаг, незавершённое. На длинные отчёты — **ссылка сюда** (`SESSION_LOG` + дата), без копипасты всего текста. |
| **`CLAUDE.md`** | Указывает читать `HANDOFF.md` в начале и дополнять его после существенной работы — имеется в виду **краткое** обновление + отсылка к `SESSION_LOG` для деталей. |

**Не размазывать** одну и ту же историю по `HANDOFF`, `CLAUDE` и разным md — детали сессии = один блок в **`SESSION_LOG.md`**.

---

## [2026-04-01] Family tree (поколения): колонки Kelly/Anderson, коннекторы, читаемость

**Контекст:** после `FAMILY_TREE_SCOPE = 'kelly_anderson'` и фиксированных колонок A/B пользователь подтвердил, что связи стали понятнее; ниже — зафиксированные замечания и решения.

| Замечание | Причина | Решение |
|-----------|---------|---------|
| Все семьи EN-демо в дереве | `full-tree` отдаёт весь граф | `FAMILY_TREE_SCOPE` в `familyTreeKellyFilter.js`: только Kelly+Anderson по последней фамилии |
| Kelly и Anderson «в одной колонке» по центру | каждый ряд центрировался по ширине холста | в `buildGenerationLayout` фиксированные ширины колонок left/center/right + выравнивание; Kelly=A, Anderson=B при обеих фамилиях в графе |
| Нет линии до второго супруга / кольца «висят» | при отсутствии зазора по X брак схлопывался в точку | `marriageBarInGap`: отрезок ненулевой ширины вокруг `mx` |
| Линии parent→child через чужие карточки (Rose) | горизональ на середине большого Δy | §3: `yH` сразу под родителем, не по середине интервала |
| Разрыв ствол↔вилка у Anderson | горизонталь вилки [xMin,xMax] не включала `mx` | расширение до `[min(xMin,mx), max(xMax,mx)]` |
| Вилка через Rose к Helen | `yFork` по середине брак↔дети попадал в промежуточный ряд | §2: `yFork` в зазоре над детским рядом (`minChildY - forkMargin`) |
| Тонкая связь брат/сестра (half_sibling и т.д.) | тонкий пунктир | §4: `strokeWidth` 2.2, пунктир `8 5`, выше непрозрачность |
| Короткая вертикаль вилка→ребёнок | малый `forkMargin` | увеличен диапазон `forkMargin` (~12–20 px по шагу ряда) |

**Файлы:** `familyTreeKellyFilter.js`, `familyTreeGenerationLayout.js`, `familyTreeOrthogonalConnectors.js`.

---

## [2026-03-31] Family tree: брат и сестра в один ряд (Kelly + Anderson)

**Проблема:** у пары родителей (Michael + Catherine) дети Sarah и Daniel отображались **вертикально** (как родитель→ребёнок), а не **на одной горизонтали**.

**Причины:**
1. В БД могло быть **ложное** ребро PARENT/CHILD между сиблингами (или инвертированные пары от старого сида).
2. BFS поколений в `full-tree` и раскладка на фронте не всегда выравнивали сиблингов без явной пары «общий родитель».

**Решение (комплекс):**

| Слой | Что сделано |
|------|-------------|
| **БД** | `backend/repair_expanded_family_rels.py`: удаление PARENT/CHILD между **Sarah ↔ Daniel** (id-зависимо), добавление **SIBLING** в обе стороны при отсутствии; то же для **George ↔ Helen** (ветка Anderson, полные сиблинги William+Agnes). Пересборка корректных PARENT/CHILD к родителям. В скрипте **`engine.echo = false`**, чтобы не заливать консоль SQL при `DEBUG=true`. |
| **API** | `backend/app/api/family.py`: в `refine_generations_parent_child` добавлены пары из **`_infer_sibling_pairs_from_shared_parents(parents_of)`** — любые двое детей с **общим родителем** получают одно поколение в `full-tree`. |
| **Фронт** | `stripSiblingConflictingParentEdges`, пересечение детей у супругов в `finalizeSiblingGenerations`, `stripSiblingConflictingParentEdges` в коннекторах и `buildGenerationLayout` — не рисовать и не считать глубину по ложному parent/child между сиблингами. |

**UI «вторая семья» (Anderson):** в `familyTreeKellyFilter.js` **`FAMILY_TREE_SCOPE`**: `'kelly_anderson'` — узлы с последней фамилией **Kelly** или **Anderson** (остальные семьи API не рисуем); `'kelly'` — только Kelly; `'full'` — весь граф.

**Запуск ремонта БД:** из `backend/`: `python repair_expanded_family_rels.py`

**Подтверждение:** после правок дерево отображается как задумано (сиблинги в один ряд под родителями; вторая ветка — Anderson — при `FAMILY_TREE_KELLY_ONLY = false`).

---

## [2026-03-30] Лендинг (видео, QR на камне), чат/timeline/инвайты, перф мемориала

**Статус:** сделано в коде (часть коммитов могла быть запушена ранее; сверить `git log`).

### Лендинг (`frontend/landing/`, зеркало `landing/`)
- **Демо-видео:** секция `#demo` — `<video poster="/images/demo-poster.png" src="/video/demo.mp4">`; `frontend/landing/video/demo.mp4` в репо; `vite.config.js` — копирование `landing/video` → `dist/video`, dev-middleware с **HTTP Range** для seek.
- **`.gitignore`:** игнор дубликата `landing/video/*.mp4` в корне; канон — `frontend/landing/video/`.
- **Hero + Physical memorial:** чат с портрета перенесён **вниз слева** (не перекрывает лицо); карточка «телефона» у QR-секции — **вправо внизу** (не перекрывает цветы/основание камня).
- **Согласование копирайта с картинкой:** на фото добавлена **иллюстрация таблички с декоративным QR** (SVG) + подпись, что фото стоковое, имя/даты в цифровом мемориале после скана.

### Продукт (SPA под `/app/`)
- **Источники в чате:** список источников RAG — в **`<details>`**, по умолчанию свёрнут; ключи `chat.sources_toggle` (en/ru). Файлы: `AvatarChat.jsx`, `AvatarChat.css`, `locales/en.js`, `ru.js`.
- **Timeline API:** `GET /memorials/{id}/timeline` — сначала воспоминания **с `event_date`**, затем **без даты** (подпись «Без даты» / «No date», язык от `memorial.language`). `TimelineItem.event_date` опционален. Файлы: `memorials.py`, `schemas.py`, `LifeTimeline.jsx`, локали.
- **Инвайты «поделиться»:** создание/список/отзыв инвайта для роли **EDITOR** (раньше только OWNER → 403 у редакторов). URL приглашения на фронте: **`frontend/src/utils/inviteUrl.js`** — `buildContributeInviteUrl(token)` с учётом `import.meta.env.BASE_URL` (`/app/` на Vercel). Бэкенд: `_make_invite_url` — первый непустой из `PUBLIC_FRONTEND_URL` / `FRONTEND_URL`. Использование: `MemoryList.jsx`, `MemorialDetail.jsx` (создание ссылки).
- **Переключение между мемориалами:** в `MemorialDetail` при смене `id` — сброс вкладок на **Media**, `revokeObjectURL` для QR blob, снятие модалки QR (меньше одновременных тяжёлых вкладок).

### Тесты
- `backend/tests/test_timeline.py` — переписаны под undated + порядок dated→undated.
- `pytest tests/test_timeline.py tests/test_invites.py` — ок. Полный `pytest` в песочнице может падать на несвязанных тестах (сеть/прокси, см. `test_cover_photo`).

### Не сделано / на потом
- Отдельный **React Query / prefetch** списка мемориалов — не внедряли; только сброс вкладок при смене `id`.
- **Пуш в git** после последних правок — пользователь должен проверить `git status` и при необходимости запушить.
- Дублирующий файл `~/.claude/.../session_log.md` — при необходимости синхронизировать вручную с этим файлом (в репо источник правды — **`SESSION_LOG.md`** здесь).

### Ключевые пути кода
- Лендинг: `frontend/landing/index.html`, `frontend/vite.config.js`, `.gitignore`
- Чат: `frontend/src/components/AvatarChat.jsx`, `AvatarChat.css`
- Таймлайн: `backend/app/api/memorials.py` (`get_timeline`), `frontend/src/components/LifeTimeline.jsx`
- Инвайты: `backend/app/api/invites.py`, `frontend/src/utils/inviteUrl.js`, `MemoryList.jsx`, `MemorialDetail.jsx`

---

## [2026-03-29] Сводка сессий Cursor — консультации, код, git

Ниже — всё, что происходило в связанных сессиях чата (ответы ассистента + выполненные действия).

### 1. Обзор репозитория и «памяти»
- Прочитан **`HANDOFF.md`**: актуальный фокус на тот момент — Family Network / Family Tree, EN-демо, следующие шаги по сидам и RAG.
- Прочитан **`SESSION_LOG.md`**, упомянут **`.claude/commands/memory-audit.md`** (чеклист RAG, не журнал).
- Отдельного файла `memory.md` в корне нет: handoff — **`HANDOFF.md`**, история — **`SESSION_LOG.md`**.

### 2. Лендинг
- Подтверждено наличие **`landing/index.html`** и зеркала для сборки **`frontend/landing/index.html`**.
- В **`frontend/vite.config.js`** при production build лендинг копируется из **`frontend/landing/index.html`** в **`frontend/dist/index.html`** (корень артефакта на Vercel). Изменения в корневом `landing/` имеет смысл **дублировать** в `frontend/landing/`, если правите только один файл.

### 3. Деплой: лендинг на `/`, SPA на `/app/`
**Цель:** по домену Vercel открывается лендинг; приложение — под **`/app/*`**; CTA ведут на **`/app/login`**, **`/app/register`**.

**В коде (фиксировалось ранее в сессии):**
- **`frontend/vite.config.js`:** при `build` — `base: '/app/'`, `outDir: 'dist/app'`, плагин в `closeBundle` копирует лендинг в `dist/index.html`; при dev — `base: '/'`, порт по умолчанию **5173** (если локально **5174** — отдельный запуск/настройка, на прод не влияет).
- **`frontend/src/App.jsx`:** `BrowserRouter` с `basename` из `BASE_URL` (в проде `/app`).
- **`vercel.json` (корень):** rewrites для `/app`, `/app/`, `/app/(.*)` → `/app/index.html`; **нет** общего `/(.*) → /index.html`.
- **`frontend/vercel.json`:** согласован с корнем при деплое из `frontend/`.
- **`landing/index.html` / `frontend/landing/index.html`:** ссылки на приложение, якоря в футере.
- **`backend/.env.example`:** **`FRONTEND_URL`**, **`PUBLIC_FRONTEND_URL`** с суффиксом **`/app`** для прод; комментарии к OAuth (`.../app/auth/callback`).

**Проверка сборки:** `cd frontend && npm run build` → `dist/index.html` (лендинг) + `dist/app/` (SPA + assets).

### 4. Консультации (без изменения кода в тот момент)
- **Vercel + репозиторий:** деплой из **текущего репо**, отдельная ветка только под лендинг не обязательна; «пуш только лендинга» данных не даёт — нужна полная сборка.
- **ElevenLabs:** план **Creator** часто достаточен для пилота; **Pro** — при выходе за лимиты символов/нагрузки, не как обязательный минимум.
- **Оживление фото:** сравнение **D-ID / HeyGen / Hedra / self-hosted**; что можно попробовать бесплатно (trial/веб) и где есть **официальный API**; у **Hedra** API обычно с платного плана.
- **Self-hosted (SadTalker и т.д.):** «бесплатно по деньгам» ≈ нет оплаты вендору за секунду, но **есть** стоимость GPU/времени и **своя** эксплуатация API.
- **Чеклист «всё работает в вебе»:** фазы: Postgres + S3, деплой бэкенда и env, Google OAuth URI, **`VITE_API_URL`** на Vercel, публичные URL для медиа/D-ID, проверка маршрутов (см. также `ENVIRONMENT.md`).
- **MCP:** в чате Cursor ассистенту доступны только переданные инструменты; список MCP в Cursor он не видит; **Claude Code** — отдельный контекст от Cursor.

### 5. Синхронизация мемориалов локально ↔ прод
- **`git push` не переносит** `*.db`, `uploads/` (в `.gitignore`).
- Совпадение данных: **одна `DATABASE_URL`** (например Supabase) для локального и прод-бэкенда + сиды; медиа — общий **S3** при **`USE_S3=true`**.

### 6. Git: проверка и push
- До коммита: много **modified** и **untracked**; ветка отслеживала `origin/main`.
- Выполнено ассистентом: **`git add -A`** (с учётом `.gitignore`), коммит и push.
- **Коммит `0afa1a3`** → **`main`**, remote при push: `https://github.com/alexeikalinin/memorial-mvp.git` (у себя сверить: `git remote -v`).
- Сообщение коммита: *Sync: EN memorials seeds, Family Tree UX, landing /app CTAs, deploy docs* — **58 файлов** (сиды, бэкенд, фронт, лендинг, docs, e2e, bot, `.claude` commands, превью и пр.).

### 7. Обновления журналов в сессии
- В **`SESSION_LOG.md`** и **`HANDOFF.md`** добавлены пометки про схему **`/app`** и ссылка друг на друга.

### 8. Чеклист для ревью (Claude Code / прод)
- [ ] `vite.config.js`: dev не сломан; путь к лендингу **`frontend/landing/index.html`** в CI существует.
- [ ] SPA с `basename`: маршруты `/m/:id`, `/contribute/:token`, `/auth/callback` в проде под **`/app/...`**.
- [ ] Vercel: **`VITE_API_URL=https://<backend>/api/v1`**, redeploy после смены env.
- [ ] Бэкенд прод: **`FRONTEND_URL`** и **`PUBLIC_FRONTEND_URL`** с **`/app`**.
- [ ] Google OAuth: redirect бэкенда ок; финальный редирект на **`FRONTEND_URL/auth/callback`** совпадает с развёрнутым SPA.
- [ ] `/` отдаёт статический лендинг, не SPA.

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
