# Handoff — Memorial MVP
> Автообновлено: 2026-09-23 13:07
> Ветка: main

## Последний коммит
5fc2459 fix: redirect already-authenticated users away from /login and /register

## Изменённые файлы (uncommitted)
- HANDOFF.md
- backend/.env.example
- backend/app/api/ai.py
- backend/app/config.py
- backend/app/main.py
- backend/app/models.py
- backend/app/schemas.py
- backend/app/services/ai_tasks.py
- frontend/landing/index.html

## Новые файлы (untracked)
- .claude/agents/vspomin-design-agent.md
- .claude/skills/testing-jwt-token-security/LICENSE
- .claude/skills/testing-jwt-token-security/SKILL.md
- .claude/skills/testing-jwt-token-security/references/api-reference.md
- .claude/skills/testing-jwt-token-security/scripts/agent.py

## Последние 3 коммита
5fc2459 fix: redirect already-authenticated users away from /login and /register
34f2015 docs: refresh HANDOFF.md session state
ac20243 fix: hero button hover glitch, new-user onboarding redirect, landing demo updates

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
