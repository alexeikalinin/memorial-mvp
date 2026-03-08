# 🚀 Инструкция по запуску приложения

## Быстрый старт

### Вариант 1: Автоматический запуск (Backend)

```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp
./start_all.sh
```

Это запустит Backend в текущем терминале.

### Вариант 2: Ручной запуск (рекомендуется)

Откройте **4 терминала** и выполните команды ниже.

---

## Терминал 1: Backend (FastAPI)

```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Ожидаемый результат:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## Терминал 2: Frontend (React/Vite)

```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/frontend
npm run dev
```

**Ожидаемый результат:**
```
VITE v5.4.21  ready in XXX ms
➜  Local:   http://localhost:5173/
```

---

## Терминал 3: Celery Worker

```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend
source .venv/bin/activate
celery -A app.workers.worker worker --loglevel=info
```

**Ожидаемый результат:**
```
celery@... ready.
[tasks]
  . animate_photo
  . create_memory_embedding
```

---

## Терминал 4: Ngrok (для публичного доступа)

```bash
ngrok http 8000
```

**Ожидаемый результат:**
```
Forwarding  https://xxx.ngrok-free.app -> http://localhost:8000
```

**Важно:** После запуска ngrok:
1. Скопируйте HTTPS URL (например: `https://xxx.ngrok-free.app`)
2. Добавьте в `backend/.env`:
   ```env
   PUBLIC_API_URL=https://xxx.ngrok-free.app
   ```
3. Backend автоматически перезагрузится

---

## Проверка работы

1. **Backend API:** http://localhost:8000/docs
2. **Frontend:** http://localhost:5173
3. **Redis:** `redis-cli ping` (должно вернуть `PONG`)

---

## Остановка всех процессов

В каждом терминале нажмите `Ctrl+C`

Или выполните в любом терминале:
```bash
pkill -f "uvicorn|vite|celery.*worker|ngrok"
```

---

## Порядок запуска

1. ✅ Redis (должен быть запущен)
2. ✅ Backend (Терминал 1)
3. ✅ Frontend (Терминал 2)
4. ✅ Celery Worker (Терминал 3)
5. ✅ Ngrok (Терминал 4) - опционально, но рекомендуется для HeyGen

---

## Если что-то не работает

1. Проверьте, что Redis запущен: `redis-cli ping`
2. Проверьте логи в каждом терминале
3. Убедитесь, что все зависимости установлены
4. Проверьте, что порты 8000, 5173, 6379 не заняты

---

## Быстрая проверка

```bash
# Проверка Redis
redis-cli ping

# Проверка процессов
ps aux | grep -E "uvicorn|vite|celery|ngrok" | grep -v grep
```

---

**Готово!** Теперь можно работать с приложением. 🎉

