# Handoff — Memorial MVP
> Обновлено: 2026-10-07
> Ветка: main

## Текущий фокус
Выбор/кадрирование фото мемориала и отдельного аватара, личный альбом с viewer; user разрешил push/deploy и веб-проверку. Генерации аватара — следующий этап, домены отложены.

## Последнее действие
Production обновлён (b7884a0 + 18c5862); Railway SUCCESS после увеличения startup healthcheck до 120s. В Chrome проверены save/reload crop, independent avatar/reset follow, album open/Escape на demo 10. В Fish Audio Test 318 пока нет фото.
Реализованы новый editor, сохранение crop/source в portrait_settings JSON (additive startup migration), cover/avatar derived endpoints, независимый портрет аватара с возвратом к cover. Gallery убрала старое оживление и добавила multi-upload и candle viewer. Backend tests/image contract passed, frontend build и lint новых компонентов passed. Подробности: [SESSION_LOG.md](SESSION_LOG.md).

## Следующий шаг
Осталось live проверить загрузку нескольких новых файлов и листание нескольких фото; основной editor save/reload уже проверен. Fish Audio voice production проверен, Fish video backend transport ещё не реализован. HeyGen сохранён. Окружения: [ENVIRONMENT.md](ENVIRONMENT.md).
