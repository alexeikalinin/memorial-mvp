# Handoff — Memorial MVP
> Автообновлено: 2026-09-25 16:51
> Ветка: main

## Последний коммит
faa58a2 fix: mobile nav menu and focus-visible accessibility on landing page

## Изменённые файлы (uncommitted)
- HANDOFF.md
- backend/app/api/ai.py
- backend/app/services/ai_tasks.py
- frontend/src/api/client.js
- frontend/src/components/AvatarChat.css
- frontend/src/components/AvatarChat.jsx
- frontend/src/locales/en.js
- frontend/src/locales/ru.js
- frontend/vite.config.js

## Новые файлы (untracked)
- .claude/agents/vspomin-design-agent.md
- .claude/skills/testing-jwt-token-security/LICENSE
- .claude/skills/testing-jwt-token-security/SKILL.md
- .claude/skills/testing-jwt-token-security/references/api-reference.md
- .claude/skills/testing-jwt-token-security/scripts/agent.py

## Последние 3 коммита
faa58a2 fix: mobile nav menu and focus-visible accessibility on landing page
851fb82 feat: add Fish Audio as alternative TTS/voice-cloning provider
5fc2459 fix: redirect already-authenticated users away from /login and /register

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
