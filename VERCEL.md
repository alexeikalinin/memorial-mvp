# Деплой на Vercel и настройка для работы с backend и чатом с ИИ

На Vercel деплоится **только фронтенд** (React). Backend (FastAPI) нужно поднять отдельно (Railway, Render, Fly.io и т.д.). Чат с ИИ-аватаром работает только если backend доступен по URL и настроены ключи API на стороне backend.

---

## 1. Настройка проекта в Vercel

В **корне репозитория** лежит `vercel.json`: в нём заданы сборка из папки `frontend/`, вывод в `frontend/dist` и правила для SPA (все маршруты отдают `index.html`). При деплое с корня репо **ничего в настройках Vercel менять не нужно** — достаточно подключить репозиторий и задеплоить.

### Вариант А: деплой с корня (рекомендуется)

- **Root Directory** оставьте пустым (корень репо).
- Сборка и вывод заданы в `vercel.json`: `installCommand`/`buildCommand` заходят в `frontend/`, `outputDirectory` = `frontend/dist`.

### Вариант Б: Root Directory = `frontend`

Если в **Project Settings** → **General** → **Root Directory** указать **`frontend`**:

- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

Тогда используется `frontend/vercel.json` (только rewrites для SPA).

---

## 2. Переменные окружения в Vercel

В **Project Settings** → **Environment Variables** добавьте:

| Переменная       | Значение | Где взять |
|------------------|----------|-----------|
| `VITE_API_URL`   | Полный URL backend **без** завершающего слеша, с путём `/api/v1`. Пример: `https://your-backend.railway.app/api/v1` | URL вашего задеплоенного backend |

- Имя **обязательно** `VITE_API_URL` — так фронт подставляет URL в сборку.
- Без этой переменной фронт будет ходить на относительный путь `/api/v1` (то есть на тот же Vercel-домен), запросы уйдут в 404, список мемориалов и чат с аватаром работать не будут.

После добавления переменной имеет смысл сделать **Redeploy**, чтобы пересобрать проект с новым значением.

---

## 3. Backend (отдельный хостинг)

Backend нужно задеплоить на любом сервисе (Railway, Render, Fly.io, и т.д.) и получить его публичный URL, например:  
`https://memorial-api.railway.app`

### CORS на backend

В `.env` backend (или в переменных окружения на хостинге) укажите домен Vercel в CORS:

```env
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-*.vercel.app
```

Подставьте реальный домен вашего Vercel-проекта (и с префиксом `*` для превью-деплоев, если нужно).

### Чтобы работал чат с ИИ-аватаром

Всё это настраивается **на backend** (переменные окружения сервера, где крутится FastAPI), не в Vercel:

| Переменная (backend) | Назначение |
|----------------------|------------|
| `OPENAI_API_KEY`     | Ответы и эмбеддинги для RAG |
| `VECTOR_DB_PROVIDER` | `qdrant` или `pinecone` |
| Для Qdrant: `QDRANT_URL` или Qdrant Cloud; для Pinecone: `PINECONE_*` | Хранение эмбеддингов воспоминаний |
| `ELEVENLABS_API_KEY` (опционально) | Озвучка ответов аватара |
| `DID_API_KEY` или HeyGen (`USE_HEYGEN=true`, `HEYGEN_API_KEY`) | Анимация фото (если нужна) |
| `PUBLIC_API_URL`     | Публичный URL backend (для webhook’ов и т.п.) |

Фронт только шлёт запросы на `VITE_API_URL`; чат с аватаром отвечает, когда backend по этому URL доступен и перечисленные ключи на backend заданы.

---

## 4. Краткий чеклист

- [ ] В Vercel: **Root Directory** = `frontend`
- [ ] В Vercel: переменная **`VITE_API_URL`** = `https://ВАШ_BACKEND_URL/api/v1`
- [ ] Backend задеплоен и доступен по этому URL
- [ ] На backend: **CORS** разрешает домен Vercel (`CORS_ORIGINS`)
- [ ] На backend: заданы **OPENAI_API_KEY** и векторная БД (Qdrant/Pinecone) для работы чата с ИИ
- [ ] После смены `VITE_API_URL` сделан **Redeploy** в Vercel

После этого деплой на Vercel должен открываться, данные и чат с ИИ-аватаром — работать через ваш backend.
