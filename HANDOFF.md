# Handoff — Memorial MVP
> Обновлено: 2026-03-15

## Что сейчас делается
Оптимизация UX: быстрое переключение вкладок + аватарки в семейном дереве — завершено.

## Последнее действие
- `MemorialDetail.jsx` — lazy mounting вкладок: компоненты монтируются один раз, скрываются через `display:none`
- `FamilyTree.jsx` — исправлен источник URL аватарок: теперь `getMediaUrl(node.cover_photo_id, 'small')`
- `backend/app/api/family.py` — `get_family_tree` переписан с N+1 на bulk BFS (3 запроса вместо N*2+)
- `backend/app/schemas.py` — `FamilyTreeNode.cover_photo_url` → `cover_photo_id`

## Следующий шаг
Протестировать семейное дерево — убедиться, что аватарки отображаются. Деплой в Railway при необходимости.

## Незавершённые задачи
- (нет)

## Изменённые файлы (текущая сессия)
- `frontend/src/pages/MemorialDetail.jsx` — lazy mounting вкладок через `mountedTabs` Set
- `frontend/src/components/FamilyTree.jsx` — `cover_photo_id` + `getMediaUrl`
- `backend/app/schemas.py` — `FamilyTreeNode`: `cover_photo_url` → `cover_photo_id`
- `backend/app/api/family.py` — BFS bulk queries в `get_family_tree`

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Критический контекст
- **Аватарки**: backend возвращал относительный URL `/api/v1/media/...`, который в продакшне (Vercel + Railway) уходил на Vercel. Решение: передавать `cover_photo_id`, фронтенд строит URL через `getMediaUrl()` с учётом `VITE_API_URL`.
- **Lazy mounting**: `mountedTabs` Set пополняется при первом клике. Раньше каждый клик = unmount+remount+повторные API запросы.
