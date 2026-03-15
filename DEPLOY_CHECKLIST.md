# Чеклист деплоя: Vercel + Backend

**Только локальный запуск?** → см. [RUN_LOCAL.md](./RUN_LOCAL.md) (один ключ OpenAI, две команды).

**CORS:** домен `https://memorial-mvp.vercel.app` уже прописан в бэкенде по умолчанию — дополнительно задавать CORS на сервере не нужно.

Подставьте **свои** значения в блоки ниже и выполните по шагам.

---

## Шаг 1. Домен фронта на Vercel

После деплоя репозитория на Vercel откройте проект и посмотрите URL, например:

- `https://memorial-mvp.vercel.app`  
или  
- `https://ваш-проект-xxxx.vercel.app`

**Ваш домен (для шага 4):**

```
МОЙ_VERCEL_URL = https://memorial-mvp.vercel.app
```

---

## Шаг 2. URL бэкенда — где взять

**Откуда берётся `https://ВАШ_БЭКЕНД_URL`:** вы загружаете backend (папку `backend/` или весь репо) на хостинг, который запускает Python/FastAPI. Сервис после деплоя выдаёт вам публичный URL. Этот URL и есть «ваш backend URL».

| Сервис | Как получить URL |
|--------|-------------------|
| **Railway** | [railway.app](https://railway.app) → New Project → Deploy from GitHub (выберите репо, корень или папку `backend`). В настройках сервиса: **Settings** → **Networking** → **Generate Domain**. Появится URL вида `https://memorial-mvp-production-xxxx.up.railway.app` — это и есть ваш backend URL. |
| **Render** | [render.com](https://render.com) → New → Web Service → подключаете репо. **Root Directory** укажите `backend`. Build: `pip install -r requirements.txt`, Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. После деплоя Render даст URL вида `https://memorial-mvp-xxxx.onrender.com`. |
| **Fly.io** | Установите [flyctl](https://fly.io/docs/hands-on/install-flyctl/), в папке `backend/`: `fly launch` и `fly deploy`. URL будет вида `https://ваш-проект.fly.dev`. |

**Итог:** скопируйте выданный хостингом URL (без `/api/v1` и без слеша в конце) — это и есть **МОЙ_BACKEND_URL**. В Vercel в `VITE_API_URL` подставляете: `https://МОЙ_BACKEND_URL/api/v1`.

---

## Шаг 3. Vercel: переменная окружения

1. Vercel → ваш проект → **Settings** → **Environment Variables**.
2. Добавьте переменную:

| Name           | Value                              |
|----------------|------------------------------------|
| `VITE_API_URL` | `https://МОЙ_BACKEND_URL/api/v1`   |

**Пример:** если `МОЙ_BACKEND_URL = https://memorial-mvp-api.railway.app`, то:

```
VITE_API_URL = https://memorial-mvp-api.railway.app/api/v1
```

3. **Save** → **Redeploy** (Deployments → ⋮ у последнего деплоя → Redeploy).

---

## Шаг 4. Backend: CORS

**Уже настроено:** в коде бэкенда по умолчанию разрешён origin `https://memorial-mvp.vercel.app`. Ничего задавать не нужно.

Если будете использовать превью-деплои Vercel (другие URL), добавьте их в переменную на сервере:

```
CORS_ORIGINS=http://localhost:5173,https://memorial-mvp.vercel.app,https://ваш-превью.vercel.app
```

Шаблон остальных переменных backend: `backend/.env.example`.

---

## Шаг 5. Backend: чат с ИИ-аватаром (опционально)

Нужны **OPENAI_API_KEY** (берёте в [platform.openai.com](https://platform.openai.com/api-keys)) и **векторная БД** для хранения эмбеддингов воспоминаний. Что именно задать — ниже.

---

### Векторная БД — что предоставить

В коде используется либо **Qdrant**, либо **Pinecone**. Выберите один вариант и задайте переменные на том же сервере, где крутится backend.

#### Вариант A: Qdrant

| Что | Где взять | Переменные на backend |
|-----|-----------|------------------------|
| **Локальный Qdrant (только для разработки)** | Запуск в Docker: `docker run -p 6333:6333 qdrant/qdrant`. На том же сервере, где backend. | `VECTOR_DB_PROVIDER=qdrant`<br>`QDRANT_URL=http://localhost:6333` |
| **Файловый режим (без сервера Qdrant)** | Ничего поднимать не нужно — данные в папке на диске. | `VECTOR_DB_PROVIDER=qdrant`<br>`QDRANT_LOCAL_PATH=./qdrant_storage` |
| **Qdrant Cloud** | [cloud.qdrant.io](https://cloud.qdrant.io) → регистрация → создайте кластер → в дашборде: **Cluster** → URL кластера и **API Key**. | `VECTOR_DB_PROVIDER=qdrant`<br>`QDRANT_URL=https://xxxxx-xxxxx.aws.cloud.qdrant.io:6333`<br>`QDRANT_API_KEY=ваш_api_key` |

Имя коллекции по умолчанию: `memorial-memories` (можно не менять). При необходимости переопределяется через `QDRANT_COLLECTION_NAME`.

#### Вариант B: Pinecone

| Что | Где взять | Переменные на backend |
|-----|-----------|------------------------|
| **Pinecone** | [pinecone.io](https://www.pinecone.io) → регистрация → **Create Index** (dimension: **1536** для `text-embedding-3-small`). В **API Keys** скопируйте ключ и в **Index** — host (environment) и имя индекса. | `VECTOR_DB_PROVIDER=pinecone`<br>`PINECONE_API_KEY=ваш_api_key`<br>`PINECONE_ENVIRONMENT=us-east-1-aws` (или из дашборда)<br>`PINECONE_INDEX_NAME=memorial-memories` (или имя вашего индекса) |

---

**Кратко:** для продакшена удобнее **Qdrant Cloud** (бесплатный тир) или **Pinecone** (тоже есть free tier). Для быстрого старта без регистрации в облаке — на сервере backend задайте `QDRANT_LOCAL_PATH=./qdrant_storage` (папка создаётся автоматически).

---

## Проверка

1. Откройте **МОЙ_VERCEL_URL** в браузере.
2. Должна загрузиться главная; если backend доступен и CORS настроен — появятся мемориалы (или пустой список).
3. Откройте мемориал → вкладка «Чат» — при настроенных ключах на backend аватар будет отвечать.

Если список не грузится: проверьте `VITE_API_URL` и сделайте Redeploy; если запросы блокируются в консоли (CORS) — проверьте `CORS_ORIGINS` на backend.

---

## Что нужно ещё (кратко)

| Где | Что сделать |
|-----|-------------|
| **Vercel** | Добавить переменную **`VITE_API_URL`** = `https://ВАШ_БЭКЕНД_URL/api/v1` (URL того сервера, где крутится FastAPI). После этого — **Redeploy**. |
| **Backend** | Задеплоить на Railway / Render / Fly.io и т.д. CORS для `memorial-mvp.vercel.app` уже прописан в коде. |
| **Чат с ИИ** | На backend задать **OPENAI_API_KEY** и векторную БД (Qdrant или Pinecone). Без этого чат с аватаром не будет отвечать. |
