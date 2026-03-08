Создай новый API endpoint в проекте memorial-mvp.

Аргумент: $ARGUMENTS — описание endpoint (например: "POST /api/v1/ai/summarize — суммаризация воспоминаний мемориала")

## Шаг 1: Изучи архитектуру

Прочитай параллельно:
- `backend/app/schemas.py` — существующие Pydantic схемы
- `backend/app/models.py` — DB модели
- `backend/app/api/ai.py` — пример AI endpoint (для AI-фич)
- `backend/app/api/memorials.py` — пример CRUD endpoint (для CRUD-фич)
- `backend/app/main.py` — как регистрируются роутеры

## Шаг 2: Определи, куда добавить

На основе $ARGUMENTS реши:
- AI-функция (OpenAI, D-ID, ElevenLabs) → `backend/app/api/ai.py`
- CRUD мемориалов/медиа/воспоминаний → `backend/app/api/memorials.py`
- Новая отдельная сущность → новый файл `backend/app/api/<name>.py` + регистрация в `main.py`
- Нужна фоновая задача (долгая операция) → `backend/app/workers/worker.py`

## Шаг 3: Создай схемы

Добавь в `backend/app/schemas.py`:
```python
class <Name>Request(BaseModel):
    # поля запроса

class <Name>Response(BaseModel):
    # поля ответа
```

## Шаг 4: Реализуй endpoint

Boilerplate для AI endpoint:
```python
@router.post("/<path>", response_model=<Name>Response)
async def <function_name>(
    request: <Name>Request,
    db: Session = Depends(get_db)
):
    """Описание endpoint."""
    # 1. Получи данные из БД если нужно
    # 2. Вызови AI сервис из ai_tasks.py
    # 3. Верни результат
    pass
```

Boilerplate для CRUD endpoint:
```python
@router.post("/<path>", response_model=<Name>Response)
async def <function_name>(
    <id>: int,
    request: <Name>Request,
    db: Session = Depends(get_db)
):
    """Описание endpoint."""
    obj = db.query(<Model>).filter(<Model>.id == <id>).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    # логика
    return obj
```

## Шаг 5: Добавь метод в frontend/src/api/client.js

```javascript
// в соответствующий объект (aiAPI, memorialsAPI и т.д.)
<methodName>: (data) => api.post('/api/v1/<path>', data),
```

## Шаг 6: Проверь

Выведи:
1. Какие файлы изменены/созданы
2. Пример curl-запроса для тестирования:
```bash
curl -X POST http://localhost:8000/api/v1/<path> \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
```
3. Нужно ли запустить pytest: `cd backend && python -m pytest tests/ -v -k "<test_name>"`
