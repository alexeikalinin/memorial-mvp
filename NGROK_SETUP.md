# Настройка ngrok для HeyGen

## Проблема
HeyGen не может получить доступ к изображениям по localhost URL. Нужен публичный URL.

## Решение: Использовать ngrok

### Шаг 1: Установка ngrok (уже установлен)
```bash
brew install ngrok
```

### Шаг 2: Авторизация в ngrok (если требуется)
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```
Получить токен можно на https://dashboard.ngrok.com/get-started/your-authtoken

### Шаг 3: Запуск ngrok туннеля
В отдельном терминале:
```bash
ngrok http 8000
```

### Шаг 4: Получение публичного URL
После запуска ngrok покажет что-то вроде:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

Скопируйте URL `https://abc123.ngrok-free.app` (ваш будет другой)

### Шаг 5: Добавление в .env
Добавьте в файл `backend/.env`:
```env
PUBLIC_API_URL=https://abc123.ngrok-free.app
```

### Шаг 6: Перезапуск backend
Backend автоматически перезагрузится (если запущен с `--reload`), или перезапустите вручную.

## Альтернатива: Использовать S3
Если не хотите использовать ngrok, можно настроить S3 хранилище:
```env
USE_S3=true
S3_BUCKET_NAME=your-bucket
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

## Проверка
После настройки попробуйте анимировать фото - должно работать быстрее и без ошибок.

