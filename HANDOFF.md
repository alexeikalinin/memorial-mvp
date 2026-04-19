# Handoff — Memorial MVP
> Автообновлено: 2026-04-19 22:26
> Ветка: main

## Последний коммит
e0127ad tests: bypass billing guards in conftest; fix 402 on multi-memorial tests

## Изменённые файлы (uncommitted)
- HANDOFF.md
- backend/app/api/ai.py
- backend/app/models.py
- backend/app/schemas.py
- backend/app/services/billing.py
- backend/seed_ensure_owner.py
- backend/tests/test_ai_mocked.py
- docs/MONETIZATION.md
- docs/TEST_PLAN.md
- e2e/tests/auth.spec.js

## Новые файлы (untracked)
- docs/ACCESS_LEVELS.md

## Последние 3 коммита
e0127ad tests: bypass billing guards in conftest; fix 402 on multi-memorial tests
3356c48 media: use file_url for S3 fallback redirect; migrate seed portraits to Supabase Storage
2d4409a startup: auto-rebuild embeddings in background if Qdrant collection empty

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
