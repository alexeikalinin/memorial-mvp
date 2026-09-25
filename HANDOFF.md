# Handoff — Memorial MVP
> Автообновлено: 2026-09-23 13:14
> Ветка: main

## Последний коммит
851fb82 feat: add Fish Audio as alternative TTS/voice-cloning provider

## Изменённые файлы (uncommitted)
- HANDOFF.md
- frontend/landing/index.html

## Новые файлы (untracked)
- .claude/agents/vspomin-design-agent.md
- .claude/skills/testing-jwt-token-security/LICENSE
- .claude/skills/testing-jwt-token-security/SKILL.md
- .claude/skills/testing-jwt-token-security/references/api-reference.md
- .claude/skills/testing-jwt-token-security/scripts/agent.py

## Последние 3 коммита
851fb82 feat: add Fish Audio as alternative TTS/voice-cloning provider
5fc2459 fix: redirect already-authenticated users away from /login and /register
34f2015 docs: refresh HANDOFF.md session state

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
