# Handoff — Memorial MVP
> Автообновлено: 2026-04-17 00:36
> Ветка: main

## Последний коммит
98a472f embeddings: admin rebuild-all endpoint (X-Admin-Key)

## Изменённые файлы (uncommitted)
- .gitignore
- ENVIRONMENT.md
- HANDOFF.md
- SESSION_LOG.md
- backend/.env.example
- backend/app/api/ai.py
- backend/app/api/memorials.py
- backend/app/main.py
- backend/app/models.py
- backend/app/schemas.py

## Новые файлы (untracked)
- .claude/commands/idea.md
- backend/app/services/billing.py
- backend/clear_en_demo_covers.py
- backend/fix_robert_patricia_ex_spouse.py
- backend/portrait_params_en.py

## Последние 3 коммита
98a472f embeddings: admin rebuild-all endpoint (X-Admin-Key)
d574d48 Home: hide EN demo memorials by default; sharper images; chat TTS off; ElevenLabs quota
6d50ca0 Waitlist: POST /waitlist, landing modal, DB waitlist_signups

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
