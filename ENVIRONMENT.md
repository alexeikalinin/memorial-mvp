# Локальная разработка и деплой (Memorial MVP)

Одна кодовая база; переключение между **локально** и **веб** делается переменными окружения, без ветвления логики в коде (кроме уже существующих `import.meta.env` / `pydantic-settings`).

---

## 1. Быстрая схема

| Что | Локально | Веб (типично: Vercel + Railway/Render) |
|-----|----------|----------------------------------------|
| Фронт | `npm run dev` → [http://localhost:5173](http://localhost:5173) | Сборка `npm run build`, статика на CDN |
| Бэкенд | `uvicorn` → `http://localhost:8000` | Отдельный хост с публичным HTTPS URL |
| API с точки зрения браузера | Прокси Vite: `/api` → `8000`, см. [frontend/vite.config.js](frontend/vite.config.js) | Прямой URL бэкенда через `VITE_API_URL` |
| База | `DATABASE_URL=sqlite:///./memorial.db` | PostgreSQL (например Supabase pooler) |
| Медиа | `USE_S3=false` → файлы в `backend/uploads/` | `USE_S3=true` + ключи S3/Supabase Storage |
| CORS | `http://localhost:5173` уже в дефолтах | Добавить домен фронта в `CORS_ORIGINS` |
| Публичные ссылки (QR, внешние API) | `PUBLIC_API_URL`, `PUBLIC_FRONTEND_URL` на localhost/ngrok при необходимости | Реальные HTTPS URL бэкенда и фронта |

---

## 2. Фронтенд (`frontend/`)

| Переменная | Локально | Прод |
|------------|----------|------|
| `VITE_API_URL` | **Не задавать** или закомментировать: тогда используется относительный путь `/api/v1` и срабатывает прокси Vite на `localhost:8000`. Альтернатива: `VITE_API_URL=http://localhost:8000/api/v1` | `https://<ваш-backend>/api/v1` (без слеша в конце) |

Файл-шаблон: [frontend/.env.example](frontend/.env.example). Рабочие значения для локальной машины — в **`frontend/.env.local`** (не коммитить).

Пересборка на Vercel: после смены `VITE_API_URL` нужен **Redeploy**, т.к. Vite подставляет env на этапе сборки.

Код опоры: [frontend/src/api/client.js](frontend/src/api/client.js) — `import.meta.env.VITE_API_URL || '/api/v1'`.

---

## 3. Бэкенд (`backend/`)

Шаблон: [backend/.env.example](backend/.env.example). Рабочий файл: **`backend/.env`** (не коммитить).

| Переменная | Локально | Прод |
|------------|----------|------|
| `DATABASE_URL` | `sqlite:///./memorial.db` | Строка PostgreSQL (pooler Supabase и т.д.) |
| `USE_S3` | `false` | `true`, если медиа в облаке |
| `SUPABASE_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Пусто при `USE_S3=false` | Заполнить по Storage dashboard |
| `CORS_ORIGINS` | `http://localhost:5173` достаточно | Список через запятую: `https://<vercel-app>.vercel.app` и preview `*.vercel.app` при необходимости |
| `PUBLIC_API_URL` | `http://localhost:8000` или URL ngrok для D-ID/HeyGen | `https://<backend-host>` |
| `PUBLIC_FRONTEND_URL` | `http://localhost:5173` | URL фронта на Vercel |
| `OPENAI_API_KEY`, `QDRANT_*`, `ELEVENLABS_*` | Свои ключи | Те же или отдельные ключи/квоты для прода |
| `REDIS_URL` | `redis://localhost:6379/0` или закомментировать, если воркер не используется | URL Redis на хостинге |
| `BOT_API_BASE_URL` | `http://localhost:8000/api/v1` | Публичный `https://.../api/v1` для Telegram-бота |

Загрузка конфига: [backend/app/config.py](backend/app/config.py) — всегда читает `backend/.env`.

---

## 4. Векторная БД (Qdrant)

| Режим | Настройка |
|-------|-----------|
| Локально без Docker | `QDRANT_LOCAL_PATH` в `.env` → embedded/путь (см. комментарии в `.env.example`) или поднять Qdrant на `6333` |
| Облако | `QDRANT_URL` + `QDRANT_API_KEY`, `QDRANT_LOCAL_PATH` пустой |

---

## 5. MCP-серверы (Cursor / Claude Code)

**Где смотреть, что уже установлено:** в Cursor — **Settings → MCP** (список серверов и статус). В репозитории отдельного `mcp.json` нет; глобальный конфиг хранится в данных приложения Cursor, его нельзя надёжно прочитать из git.

**Что имело смысл добавить (опционально):**

| MCP | Зачем для этого проекта |
|-----|-------------------------|
| **Git / GitHub** | Ветки, PR, issues без выхода из IDE |
| **SQLite** | Read-only запросы к локальному `memorial.db` при отладке |
| **@playwright/mcp** | Управление Chromium из агента для проверки UI на `localhost:5173` |

Пример фрагмента для `mcp.json` (Playwright — путь к `npx` подставьте свой):

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp", "--browser", "chromium"]
    }
  }
}
```

Секреты (API ключи сторонних MCP) не храните в репозитории.

---

## 6. Чеклист перед деплоем

1. Фронт: `VITE_API_URL` = публичный API бэкенда с `/api/v1`.
2. Бэкенд: `CORS_ORIGINS` содержит точный origin фронта.
3. `USE_S3` / `DATABASE_URL` соответствуют прод-схеме; медиа реально доступны по URL из БД.
4. `PUBLIC_API_URL` / `PUBLIC_FRONTEND_URL` — не localhost.
5. Перезапуск бэкенда и redeploy фронта после смены env.

---

## 7. Supabase: одна база с локалкой и вебом

Git **не** содержит `memorial.db` и `uploads/` — на Vercel после пуша подставляется только код. Чтобы «локально и в вебе был один и тот же проект», данные должны жить **в одной PostgreSQL** (обычно Supabase), а бэкенд на проде и при желании локально подключаются к **одной и той же** `DATABASE_URL`.

### Вариант A (лучший): сразу работать против Supabase Postgres

1. В [Supabase](https://supabase.com) создайте проект → **Settings → Database** → скопируйте **Connection string** (для приложений удобен **Session pooler**, порт `5432` или `6543` — как в подсказке дашборда; в строке должен быть `sslmode=require`).
2. В `backend/.env` временно или постоянно задайте:
   - `DATABASE_URL=postgresql+psycopg2://...` (или `postgresql://...` в зависимости от драйвера в проекте — см. установленный пакет, чаще `psycopg2` / `asyncpg`).
3. Установите драйвер Postgres, если ещё нет: `pip install psycopg2-binary` (или то, что уже в `requirements.txt`).
4. Запустите бэкенд один раз — таблицы создадутся через `Base.metadata.create_all` (как при SQLite).
5. Выполните сиды **уже с этой** строкой подключения:  
   `cd backend && source .venv/bin/activate && python seed_english_all.py`  
   при необходимости портреты: `seed_english_portraits.py` / `seed_prod_portraits.py` при `USE_S3=true` и ключах Storage.
6. Прод-бэкенд (Railway/Render и т.д.) использует **ту же** `DATABASE_URL` → тот же набор мемориалов и воспоминаний без отдельного «переноса».

Так вы убираете расхождение «локально 35 мемориалов, в вебе пусто»: расхождение останется только если кто-то снова переключит локальный `.env` на SQLite.

### Вариант B: уже есть данные только в SQLite — перенос в Supabase

Прямого «sqlite dump → postgres» в репозитории нет; типичные пути:

| Способ | Суть |
|--------|------|
| **pgloader** | Утилита один раз: из `.db` в строку Postgres Supabase. После импорта проверьте последовательности (`SERIAL`/`identity`) и при необходимости поправьте enum-типы. |
| **Повторный сид** | Проще всего: подключить пустой Supabase по варианту A и снова запустить `seed_english_all.py` (+ портреты) — без миграции файла SQLite, если полный дамп не обязателен. |

**Файлы из `backend/uploads/`** в git не попадают. Для совпадения картинок на проде: включите `USE_S3=true`, ключи Supabase Storage, загрузите объекты в бакет и обновите записи `media` (или используйте существующие скрипты вроде `seed_prod_portraits.py`, которые кладут файлы в S3-совместимое хранилище и пишут `file_url`).

### Кратко

- **Один источник правды** — Postgres на Supabase и одна `DATABASE_URL` у локального и прод-бэкенда.
- **Пуш в Git** синхронизирует только код; базу и медиа «подтягивают» через env и сиды/загрузку в Storage, а не через коммит.

---

## 8. Связанные файлы

- [CLAUDE.md](CLAUDE.md) — архитектура и команды запуска
- [backend/.env.example](backend/.env.example), [frontend/.env.example](frontend/.env.example) — шаблоны переменных
