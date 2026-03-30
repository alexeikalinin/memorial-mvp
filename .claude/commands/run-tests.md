# /run-tests — Запустить все тесты и выдать отчёт

Ты — тест-агент Memorial MVP. Твоя задача: запустить все тесты, собрать результаты и выдать структурированный отчёт.

## Порядок действий

### 1. Прочитай контекст
Прочитай `docs/TEST_PLAN.md` чтобы понять, что тестируется.

### 2. Запусти backend-тесты (pytest)
```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend
source .venv/bin/activate
python -m pytest tests/ -v --tb=short --no-header 2>&1
```

Собери:
- Общий счёт: PASSED / FAILED / ERROR
- Список упавших тестов с кратким описанием ошибки
- Список модулей и их статус

### 3. Проверь E2E тесты
Проверь, запущены ли backend + frontend:
```bash
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
```

Если оба сервиса живы — запусти Playwright:
```bash
cd /Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/e2e
npx playwright test --reporter=list 2>&1
```

Если сервисы не запущены — пропусти E2E, отметь в отчёте "E2E: SKIPPED (services offline)".

### 4. Обнови историю запусков в TEST_PLAN.md
Добавь строку в таблицу "История запусков":
```
| {дата} | /run-tests | pytest: X/Y, E2E: A/B | найденные баги |
```

### 5. Сформируй итоговый отчёт

Выведи в строгом формате:

```
═══════════════════════════════════════════
  ОТЧЁТ ТЕСТИРОВАНИЯ — {дата и время}
═══════════════════════════════════════════

PYTEST (backend):
  ✅ Passed:  {N}
  ❌ Failed:  {N}
  ⚠️  Errors:  {N}
  📊 Total:   {N}

E2E PLAYWRIGHT:
  ✅ Passed:  {N}  [или SKIPPED]
  ❌ Failed:  {N}
  📊 Total:   {N}

═══════════════════════════════════════════
УПАВШИЕ ТЕСТЫ:
{для каждого упавшего теста:}
  ❌ {test_id} | {название теста}
     Ошибка: {краткое описание}
     Файл: {путь:строка}

═══════════════════════════════════════════
СТАТУС: {✅ ВСЕ ТЕСТЫ ПРОШЛИ | ❌ ЕСТЬ ПАДЕНИЯ — рекомендую /test-and-fix}
```

### 6. Обнови session_log.md
Добавь запись в `/Users/alexei.kalinin/.claude/projects/-Users-alexei-kalinin-Documents-VibeCoding-memorial-mvp/memory/session_log.md`:
```
## {дата} — /run-tests
**Статус:** pytest {X}/{Y}, E2E {A}/{B}
**Упавшие тесты:** {список или "нет"}
```
