# Переезд vspomin.ai: этап 1, 10 октября 2026

## Выполнено

- Подтверждён Vercel project prj_B3C7STI6HUELC6SNUARVTdtryxMo, owner 1alexeikalinin1-3683s-projects, Root Directory `.`.
- vspomin.ai добавлен к текущему memorial-mvp; ownership verified, configuration invalid. Старый домен сохранён, новый deploy не делался.
- Vercel verify сообщает NS ns1.hoster.by / ns2.hoster.by; публичный resolver 8.8.8.8 возвращает SERVFAIL, authoritative серверы REFUSED. Нужна активация/исправление DNS-зоны у Hoster.by.
- Точные recommended records Vercel: `@ A 216.198.79.1`, `@ A 64.29.17.1`. Перед изменением сохранить текущую DNS-зону/почтовые записи. Нельзя считать SERVFAIL отсутствием почтовых записей.
- Для минимального риска этап 1 сохраняет `/app/`: главная vspomin.ai, приложение vspomin.ai/app. Удаление /app или app-поддомен — следующий независимый этап.
- Прочитаны только несекретные URL/CORS production backend. Подготовлен локальный новый brand health + CORS нового origin с сохранением старого; примеры env обновлены. Production env не изменены.

## Текущие значения production (для отката)

```
PUBLIC_API_URL=https://backend-production-e1e8.up.railway.app
PUBLIC_FRONTEND_URL=https://memorial-mvp.vercel.app
FRONTEND_URL=https://memorial-mvp.vercel.app/app
CORS_ORIGINS=http://localhost:5173,https://memorial-mvp.vercel.app,https://memorial-mvp-*.vercel.app
```

PUBLIC_FRONTEND_URL сейчас без /app: QR helper добавляет префикс, поэтому нельзя без согласованной проверки просто унифицировать все значения. Генераторы приглашений проверять отдельно; frontend строит приглашение из origin/base.

## Что нужно от владельца

1. Открыть Hoster.by → домен vspomin.ai → DNS. Проверить наличие/активацию зоны и показать доступные настройки без секретов. Сначала восстановить authoritative DNS; затем добавить точные A-записи выше, сохранив MX/TXT.
2. Railway: чтение доступно, но добавление `api.vspomin.ai` ответило Unauthorized. Нужна авторизация для изменения доменов или ручное добавление в backend → Settings → Networking → Custom Domain. Записи CNAME/TXT брать из Railway, не угадывать.
3. Google Cloud → Google Auth Platform → Branding и Clients: показать текущий branding/redirect URI без client secret. Добавить новый API callback только после готовности api-домена, сменить имя приложения на vspomin.ai, homepage/privacy/support на реальные адреса. Сохранить старый callback на время перехода.

## Следующая безопасная последовательность

Исправить DNS и подтвердить HTTPS главной и /app, затем добавить CORS origin на production (сохранить старые origins). Отдельно подключить api-domain/TLS и проверить health/media; только затем PUBLIC_API_URL, Google callback и frontend VITE_API_URL. FRONTEND_URL/PUBLIC_FRONTEND_URL менять согласованно с QR/invite/Checkout helpers. Не разворачивать весь текущий checkout: есть независимые локальные изменения лендинга и активный deployment backend, использовать точный релизный снимок + минимальный patch.

При сбое вернуть сохранённые env/deployment; старые домены и callbacks пока не удалять. Регистрация, Google login, email verify/reset, QR, invites и медиа — обязательная ручная/live проверка до перенаправления пользователей.

Проверка этапа1: health/root — 2 теста прошли на изолированной in-memory SQLite (DATABASE_URL=sqlite://). Первоначальный запуск остановился до тестов на недоступном DNS Supabase; повтор выполнялся без обращения к production-БД.
