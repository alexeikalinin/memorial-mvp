# Handoff — Memorial MVP
> Обновлено: 2026-10-07
> Ветка: main

## Текущий фокус
Выбор/кадрирование фото мемориала и отдельного аватара, личный альбом с viewer; user разрешил push/deploy и веб-проверку. Генерации аватара — следующий этап, домены отложены.

## Последнее действие
Реализованы новый editor, сохранение crop/source в portrait_settings JSON (additive startup migration), cover/avatar derived endpoints, независимый портрет аватара с возвратом к cover. Gallery убрала старое оживление и добавила multi-upload и candle viewer. Backend tests/image contract passed, frontend build и lint новых компонентов passed. Подробности: [SESSION_LOG.md](SESSION_LOG.md).

## Следующий шаг
Проверить после deploy выбор из альбома/загрузку, zoom/crop/save/reload, independent avatar/follow reset и просмотр фотографий. Fish Audio voice production проверен, Fish video backend transport ещё не реализован. HeyGen сохранён. Окружения: [ENVIRONMENT.md](ENVIRONMENT.md).
