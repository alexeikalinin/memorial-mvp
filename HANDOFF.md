# Handoff — Memorial MVP
> Обновлено: 2026-03-08 — конец сессии (лимиты Claude Code исчерпаны)

---

## СТОП-ТОЧКА

Все запланированные задачи **выполнены**, код изменён, но **не протестирован в браузере**.

---

## Что было сделано в этой сессии

### 1. Улучшение читаемости семейного дерева ✅
**Файлы:** `frontend/src/components/FamilyTree.jsx`, `frontend/src/components/FamilyTree.css`

- `renderTreeNode(node, level, relationLabel)` — новый параметр `relationLabel`
- Бейджи на карточках: синий «Ребёнок», розовый «Супруг/а», серо-лиловый «Страница»
- `.node-body` обёртка (flex row) внутри карточки — бейдж стоит над аватар+именем
- Умершие карточки: `grayscale(85%) brightness(0.88) opacity: 0.82` (было почти незаметно)
- Линия детей: `3px solid` + горизонтальные засечки `::before` у каждого ребёнка
- Линия брака: `32px` шире, символ ∞ крупнее и розовый

### 2. Family Memory Synchronization (Layer 1 + Layer 2) ✅
**Файлы:** `backend/app/schemas.py`, `backend/app/services/ai_tasks.py`, `backend/app/api/ai.py`, `frontend/src/components/AvatarChat.jsx`, `frontend/src/api/client.js`

- Cross-memorial RAG: чекбокс «Воспоминания родственников» в чате аватара
- `include_family_memories: bool` в `AvatarChatRequest`
- `search_similar_memories()` теперь принимает список `memorial_ids`
- Memory Sync Agent: `POST /ai/family/sync-memories/{id}?dry_run=true`
- Кнопка «🔄 Синхр. с семьёй» в `AvatarChat.jsx`

---

## Следующий шаг

1. Запустить стек (см. ниже)
2. Открыть мемориал → вкладка «Семейное дерево»
   - Проверить бейджи на карточках (Ребёнок / Супруг/а / Страница)
   - Умершие карточки должны быть заметно тусклее живых
   - Горизонтальные засечки у детей
3. Открыть вкладку «Чат» → проверить чекбокс и кнопку синхронизации

---

## Незавершённые задачи

- [ ] Верификация семейного дерева в браузере
- [ ] Верификация cross-memorial RAG (создать 2 мемориала, связать, включить чекбокс)
- [ ] Верификация Memory Sync Agent (кнопка + dry_run режим)

---

## Изменённые файлы (текущая сессия)

| Файл | Изменение |
|------|-----------|
| `frontend/src/components/FamilyTree.jsx` | Бейджи, node-body, relationLabel |
| `frontend/src/components/FamilyTree.css` | Стили бейджей, коннекторы, deceased |
| `backend/app/schemas.py` | `include_family_memories` поле |
| `backend/app/services/ai_tasks.py` | Cross-memorial search, sync_family_memories() |
| `backend/app/api/ai.py` | avatar_chat обновлён, новый endpoint sync-memories |
| `frontend/src/components/AvatarChat.jsx` | Чекбокс + кнопка синхронизации |
| `frontend/src/api/client.js` | syncFamilyMemories() метод |

---

## Запуск стека

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Критический контекст

- Qdrant работает локально: `QDRANT_LOCAL_PATH=./qdrant_storage` в `backend/.env`
- Аутентификации нет — `owner_id=1` хардкод везде
- Карточка FamilyTree теперь `flex-direction: column` → внутри `.node-body { display: flex; align-items: center; gap: 0.7rem }`
- `min_score` в avatar_chat = 0.1 (было 0.2, понижено для длинных текстов с размытым embedding)
