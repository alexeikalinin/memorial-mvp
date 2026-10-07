# Handoff — Memorial MVP
> Обновлено: 2026-10-07
> Ветка: main

## Текущий фокус
Стандартизация референса фото для аватара и проверка видео в production до смены доменов. Пользователь разрешил push/deploy.

## Последнее действие
Добавлен JPEG sRGB квадрат до 1024 с безопасными полями без увеличения; исходники сохраняются. Референс доступен через /media/avatar/{id}.jpg, используется в preview/анимации. 13 backend tests и frontend build прошли. 3bcb9b7 запушен и автоматически опубликован на Railway/Vercel; production референс media 37 HTTP 200, JPEG sRGB 600x600, виден в вебе. Автовыбор лица и Fish video integration остаются следующими этапами.

3acbb67 + 429b72b опубликованы напрямую на Vercel/Railway. Backend ff89ff2e-25b7-4869-9795-3f5ef1b06d70 SUCCESS; Vercel dpl_9s1XwjWEovu7ytubJTsHQm92YXvo READY. Supabase восстановлен. Реальный ответ Fish Audio в чате memorial 318 сгенерирован и воспроизведён (9 секунд), правильный провайдер виден в интерфейсе. 7 mocked AI tests passed; frontend build passed. HTTPS GitHub токен истёк; SSH-доступ подтверждён.

## Следующий шаг
Загрузить портрет и проверить видеоответ. У memorial 318 новый Fish Audio клон есть, cover_photo_id отсутствует. Fish Audio MCP видео ещё не интегрировано в backend; HeyGen/D-ID сохранены. Домены/OAuth отложены. Подробности: [SESSION_LOG.md](SESSION_LOG.md), [Fish Audio](docs/integrations/FISH_AUDIO_AVATARS.md), [окружения](ENVIRONMENT.md).
