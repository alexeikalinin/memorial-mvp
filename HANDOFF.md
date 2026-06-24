# Handoff — Memorial MVP
> Автообновлено: 2026-06-24 13:58
> Ветка: main

## Последний коммит
d81d159 feat: email verification, password reset, family RAG billing guard, viral share fix

## Изменённые файлы (uncommitted)
- HANDOFF.md
- SESSION_LOG.md
- backend/app/api/access.py
- backend/app/api/auth.py
- backend/app/api/media.py
- backend/app/api/memorials.py
- backend/app/auth.py
- backend/app/config.py
- backend/app/main.py
- backend/app/models.py

## Новые файлы (untracked)
- .claude/agents/vspomin-design-agent.md
- .claude/skills/testing-jwt-token-security/LICENSE
- .claude/skills/testing-jwt-token-security/SKILL.md
- .claude/skills/testing-jwt-token-security/references/api-reference.md
- .claude/skills/testing-jwt-token-security/scripts/agent.py

## Последние 3 коммита
d81d159 feat: email verification, password reset, family RAG billing guard, viral share fix
de96dfa feat: remove demo panel from home — link only
7da7bca feat: hide demo memorials once user has own memorials

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
