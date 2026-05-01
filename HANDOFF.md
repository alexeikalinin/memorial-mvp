# Handoff — Memorial MVP
> Автообновлено: 2026-04-30 20:00
> Ветка: main

## Последний коммит
a59e641 fix: tutorial CSS colors explicit + step 3 scroll + step 5 generic text

## Изменённые файлы (uncommitted)
- HANDOFF.md

## Новые файлы (untracked)
- .agents/skills/stripe-best-practices/SKILL.md
- .agents/skills/stripe-best-practices/references/billing.md
- .agents/skills/stripe-best-practices/references/connect.md
- .agents/skills/stripe-best-practices/references/payments.md
- .agents/skills/stripe-best-practices/references/security.md

## Последние 3 коммита
a59e641 fix: tutorial CSS colors explicit + step 3 scroll + step 5 generic text
5a8553b feat: demo tutorial — 5-step onboarding across DemoPage and MemorialPublic
234e5a4 feat: demo page fully working — landing CTA + production DB fix

## Запуск стека
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Следующий шаг
- Полный регресс `pytest` (192 теста)
- E2E с живым стеком
- Возможно: кнопка "Restart tutorial" в демо-баннере

## Критический контекст (сессия 2026-05-02)
- `--surface: #FFFFFF` в `:root` — overlay/hint компоненты обязаны использовать явные цвета, не CSS vars
- 2 живых пользователя: verameeva77@mail.ru, onemmanwarrior@gmail.com (оба free, 0 мемориалов, апрель 2026)
- Демо-аккаунт ID=1 (is_demo=True) — владелец 43 мемориалов
- SESSION_LOG.md — последняя запись: [2026-05-02] Demo tutorial
