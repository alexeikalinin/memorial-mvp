# 🚀 Инструкция по запуску приложения

## Нужно запустить 3 компонента в отдельных терминалах

---

## ✅ Терминал 1: Backend (FastAPI)

**Откройте новый терминал на вашем компьютере** (не в Cursor)

```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Что вы увидите:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Проверка:** Откройте в браузере http://localhost:8000/docs

**Оставьте этот терминал открытым!**

---

## ✅ Терминал 2: Frontend (React/Vite)

**Откройте еще один новый терминал**

```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/frontend
npm run dev
```

**Что вы увидите:**
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Проверка:** Откройте в браузере http://localhost:5173

**Оставьте этот терминал открытым!**

---

## ✅ Терминал 3: Celery Worker (для анимации фото)

**Откройте еще один новый терминал**

```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend
source .venv/bin/activate
celery -A app.workers.worker worker --loglevel=info
```

**Что вы увидите:**
```
[2024-01-XX XX:XX:XX,XXX: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-01-XX XX:XX:XX,XXX: INFO/MainProcess] celery@MacBook-Pro ready.
```

**Этот терминал покажет логи при анимации фото!**

**Оставьте этот терминал открытым!**

---

## ✅ Проверка Redis (должен быть запущен)

Redis должен быть запущен как сервис. Проверьте:

```bash
redis-cli ping
```

Должно вернуть: `PONG`

Если не работает, запустите:
```bash
brew services start redis
```

---

## 📋 Итоговая структура терминалов:

```
┌─────────────────────────────────────┐
│  Терминал 1: Backend (uvicorn)     │
│  http://localhost:8000              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Терминал 2: Frontend (npm)        │
│  http://localhost:5173              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Терминал 3: Celery Worker         │
│  (логи анимации фото)               │
└─────────────────────────────────────┘
```

---

## 🧪 Проверка работы:

1. **Backend:** http://localhost:8000/docs (должна открыться документация API)
2. **Frontend:** http://localhost:5173 (должно открыться приложение)
3. **Worker:** В терминале 3 должны быть логи подключения к Redis

---

## 🎬 Тестирование анимации фото:

1. Откройте http://localhost:5173
2. Загрузите фото в мемориал
3. Нажмите "Оживить фото"
4. **Смотрите логи в Терминале 3** - там будет видно:
   - `Downloading image from: ...`
   - `Uploading photo to HeyGen: ...`
   - `HeyGen upload response status: ...`

---

## ⚠️ Если что-то не работает:

### Backend не запускается:
- Проверьте, что порт 8000 свободен: `lsof -ti:8000`
- Убейте процесс: `kill -9 $(lsof -ti:8000)`

### Frontend не запускается:
- Проверьте, что порт 5173 свободен: `lsof -ti:5173`
- Установите зависимости: `cd frontend && npm install`

### Worker не запускается:
- Проверьте Redis: `redis-cli ping`
- Запустите Redis: `brew services start redis`

### Анимация не работает:
- Смотрите логи в Терминале 3
- Проверьте, что `HEYGEN_API_KEY` установлен в `backend/.env`
- Проверьте, что `USE_HEYGEN=true` в `backend/.env`

---

## 🛑 Остановка всех сервисов:

В каждом терминале нажмите `Ctrl+C`

Или убейте все процессы:
```bash
pkill -f uvicorn
pkill -f vite
pkill -f celery
```

---

## 📝 Быстрый старт (скопируйте команды):

**Терминал 1:**
```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

**Терминал 2:**
```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/frontend && npm run dev
```

**Терминал 3:**
```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend && source .venv/bin/activate && celery -A app.workers.worker worker --loglevel=info
```

---

**Готово! Теперь все должно работать! 🎉**

