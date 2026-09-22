# Handoff — Memorial MVP
> Автообновлено: 2026-09-21 21:48
> Ветка: main

## Последний коммит
71af212 fix: family tree hardcoded to demo family, hid real users' own memorial

## Изменённые файлы (uncommitted)
- HANDOFF.md
- backend/app/api/auth.py
- frontend/landing/images/demo-poster.png
- frontend/landing/index.html
- frontend/landing/video/DEMO_VIDEO_SCRIPT.md
- frontend/landing/video/GENERATIVE_DEMO_VIDEO_FULL_SCENARIO.md
- frontend/landing/video/demo.mp4
- frontend/landing/video/demo.vtt
- frontend/landing/video/render_landing_demo.py
- frontend/src/components/CreateMemorialHeroButton.css

## Новые файлы (untracked)
- .claude/agents/vspomin-design-agent.md
- .claude/skills/testing-jwt-token-security/LICENSE
- .claude/skills/testing-jwt-token-security/SKILL.md
- .claude/skills/testing-jwt-token-security/references/api-reference.md
- .claude/skills/testing-jwt-token-security/scripts/agent.py

## Последние 3 коммита
71af212 fix: family tree hardcoded to demo family, hid real users' own memorial
6cea34d refactor: remove redundant onboarding checklist, expand tutorial copy
7ede7f1 feat: 4-step onboarding tutorial modal + bigger hero text/candle

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
