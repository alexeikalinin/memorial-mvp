# Handoff — Memorial MVP
> Обновлено: 2026-03-28 23:20

## Что сейчас делается
Family Network visualization реализован и работает — показывает 4 семейных кластера (Kelly/Anderson, Chang, Rossi, Морозов) с 8 мостами между ними.

## Последнее действие
- Добавлен backend endpoint `GET /api/v1/family/memorials/{id}/network-clusters` (`family.py`)
- Добавлены Pydantic схемы `NetworkClustersResponse`, `NetworkCluster`, `NetworkBridge` (`schemas.py`)
- Создан `frontend/src/components/FamilyNetwork.jsx` — SVG-визуализация с островками кластеров и пунктирными мостами
- Создан `frontend/src/components/FamilyNetwork.css`
- В `MemorialDetail.jsx` добавлен переключатель Tree / Network (компонент `FamilyViewToggle`)
- Добавлен `familyAPI.getNetworkClusters()` в `client.js`
- Исправлен DB: relationship_type нормализованы в UPPERCASE (SQLAlchemy читает по именам enum)
- Добавлены пропущенные структурные связи для IDs 48-56 (Chang+Rossi семьи не были соединены)

## Следующий шаг
- Добавить портреты для Chang/Rossi (IDs 42-56) в `seed_english_portraits.py` и запустить
- Проверить как выглядит Family Network в браузере (http://localhost:5173)
- Проверить embeddings для Chang/Rossi воспоминаний

## Незавершённые задачи
- Портреты для IDs 42-56 (Chang/Rossi) — нет cover_photo_id
- Embeddings для Chang/Rossi воспоминаний: проверить завершился ли фоновый процесс
- Тест RAG-чата на нескольких мемориалах нового кластера

## Изменённые файлы (текущая сессия)
- `backend/app/api/family.py` — endpoint `/network-clusters`, импорты, STRUCTURAL_TYPES
- `backend/app/schemas.py` — NetworkClustersResponse, NetworkCluster, NetworkClusterMember, NetworkBridge
- `frontend/src/api/client.js` — `familyAPI.getNetworkClusters()`
- `frontend/src/components/FamilyNetwork.jsx` — НОВЫЙ
- `frontend/src/components/FamilyNetwork.css` — НОВЫЙ
- `frontend/src/pages/MemorialDetail.jsx` — FamilyViewToggle, import FamilyNetwork
- `frontend/src/pages/MemorialDetail.css` — стили .family-view-tabs / .family-view-btn
- DB: нормализован relationship_type; добавлены 22 структурные связи для IDs 48-56

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Критический контекст
- SQLAlchemy `Enum(RelationshipType)` читает по **именам** (PARENT, CHILD...), DB должна хранить UPPERCASE
- Cluster endpoint: `GET /api/v1/family/memorials/{id}/network-clusters`
- 4 кластера: [0] Морозов (21), [1] Kelly/Anderson (20), [2] Chang (9), [3] Rossi (6)
- 8 cross-cluster bridges с custom_label из DB
- `FamilyViewToggle` — inline компонент в конце MemorialDetail.jsx (после `export default MemorialDetail`)
- Docs index: ENVIRONMENT.md, docs/MONETIZATION.md, docs/TEST_PLAN.md, INVESTOR_DEMO_PLAN.md
