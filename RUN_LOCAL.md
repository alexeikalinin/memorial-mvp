# Запуск всего локально (минимум настроек)

Достаточно **одного ключа** (OpenAI) и **двух команд** (backend + frontend). Векторная БД и база уже работают из коробки (файлы на диске).

---

## 1. Ключ OpenAI

1. Зайдите на [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. Создайте API key (Create new secret key), скопируйте его.

---

## 2. Настройка backend

```bash
cd backend
cp .env.example .env
```

Откройте `backend/.env` и впишите свой ключ:

```env
OPENAI_API_KEY=sk-ваш-ключ-здесь
```

Остальное можно не трогать: база — SQLite (`memorial.db`), векторная БД — локальная папка `qdrant_storage` (создаётся сама).

---

## 3. Запуск

**Терминал 1 — backend:**

```bash
cd backend
source .venv/bin/activate   # или: python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Терминал 2 — frontend:**

```bash
cd frontend
npm install
npm run dev
```

Откройте в браузере: [http://localhost:5173](http://localhost:5173).

---

## 4. Через Docker (один контейнер)

Если не хотите ставить Python/Node локально:

```bash
cd backend
cp .env.example .env
# Впишите в .env: OPENAI_API_KEY=sk-...
docker-compose -f docker-compose.simple.yml up --build
```

Backend будет на [http://localhost:8000](http://localhost:8000). Фронт нужно по-прежнему запускать отдельно (`cd frontend && npm run dev`) или собрать статику и открыть через backend (если настроите раздачу).

---

## Что уже сделано в проекте

| Что | Где |
|-----|-----|
| CORS для Vercel | В коде backend по умолчанию разрешён `https://memorial-mvp.vercel.app`. |
| Векторная БД | По умолчанию `./qdrant_storage` — не нужен Qdrant Cloud и не нужен Docker с Qdrant. |
| Деплой backend | **Railway:** папка `backend/`, в репо есть `backend/railway.toml` и `Dockerfile`. **Render:** в корне репо есть `render.yaml` — в Dashboard New → Blueprint, указать этот файл. |
| Деплой frontend | Уже на Vercel; в настройках проекта задать `VITE_API_URL` = URL вашего backend + `/api/v1`. |

После деплоя backend скопируйте выданный URL и в Vercel добавьте переменную `VITE_API_URL=https://ваш-backend-url/api/v1`, затем сделайте Redeploy.
