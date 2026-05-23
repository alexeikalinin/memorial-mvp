# Handoff — Memorial MVP
> Автообновлено: 2026-05-23 03:51
> Ветка: main

## Последний коммит
de96dfa feat: remove demo panel from home — link only

## Изменённые файлы (uncommitted)
- .claude/commands/check-quotas.md
- .claude/commands/handoff.md
- .claude/commands/run-tests.md
- .claude/commands/test-and-fix.md
- ENVIRONMENT.md
- HANDOFF.md
- INVESTOR_DEMO_PLAN.md
- README.md
- SESSION_LOG.md
- TESTING_GUIDE.md

## Новые файлы (untracked)
- .agents/skills/stripe-best-practices/SKILL.md
- .agents/skills/stripe-best-practices/references/billing.md
- .agents/skills/stripe-best-practices/references/connect.md
- .agents/skills/stripe-best-practices/references/payments.md
- .agents/skills/stripe-best-practices/references/security.md

## Последние 3 коммита
de96dfa feat: remove demo panel from home — link only
7da7bca feat: hide demo memorials once user has own memorials
8c39b97 fix: hide ElevenLabs quota error for unauthenticated users

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
