# Handoff — Memorial MVP
> Автообновлено: 2026-04-23 20:32
> Ветка: main

## Последний коммит
e6d6ea6 feat: Stripe billing integration (checkout, webhook, usage, admin)

## Изменённые файлы (uncommitted)
- .gitignore
- HANDOFF.md
- backend/app/api/ai.py
- backend/app/api/invites.py
- backend/app/api/memorials.py
- backend/app/main.py
- backend/app/models.py
- backend/app/schemas.py
- backend/app/services/billing.py
- backend/seed_ensure_owner.py

## Новые файлы (untracked)
- .agents/skills/stripe-best-practices/SKILL.md
- .agents/skills/stripe-best-practices/references/billing.md
- .agents/skills/stripe-best-practices/references/connect.md
- .agents/skills/stripe-best-practices/references/payments.md
- .agents/skills/stripe-best-practices/references/security.md

## Последние 3 коммита
e6d6ea6 feat: Stripe billing integration (checkout, webhook, usage, admin)
d608938 billing: add Pro + Lifetime Pro plans, live session endpoint, pricing on landing
e0127ad tests: bypass billing guards in conftest; fix 402 on multi-memorial tests

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
См. SESSION_LOG.md — последняя запись
