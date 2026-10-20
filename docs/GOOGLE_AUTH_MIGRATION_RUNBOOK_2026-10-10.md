# Google Auth: журнал изменений и откат — 10 октября 2026

## 1. Бренд приложения — применено

Google Cloud project ID memorial-491610, number547197616113. Google Auth Platform → Branding.

- App name: было Memorial → сохранено vspomin.ai. UI подтвердил Branding changes saved.
- Authorized domains: сохранён backend-production-e1e8.up.railway.app, добавлен vspomin.ai. Старый домен пока обязателен для работающего OAuth callback; убрать после переключения callback/backend.
- Support/developer email, scopes, audience, client secrets не менялись. Home/privacy/terms были пустыми, пока не заполнялись вымышленными URL.
- Статус приложения Testing, Google в UI сообщил verification not required for current Testing status.
- Откат: Branding → App name Memorial; при полном отказе от нового домена удалить только vspomin.ai, оставить действующий callback domain. Секреты не вращать.
- Снимок: artifacts/domain-migration/google-branding.jpg.

## 2. Отображаемое имя Google Cloud проекта — применено

IAM & Admin → Settings → Project name. Google отклонил vspomin.ai из-за точки. Сохранено **vspomin ai**, UI/верхний project selector подтвердили новое имя.

- ID memorial-491610 и project number547197616113 сохранены. Название OAuth приложения остаётся vspomin.ai.
- Откат: Project name → Memorial → Save. Идентификатор и ресурсы менять не требуется.
- Снимок: artifacts/domain-migration/google-project-name.jpg.

## 3. API domain и callback — в работе

CLI Railway domain api.vspomin.ai дважды вернул Unauthorized; mutation не подтверждена. Авторизованный Railway открыт в Chrome; выбранный production проект Memorial IDdb2a7084-b8be-4a74-94d7-6e6a466f4fe2, backend service3d5373bc-9885-4cc2-b466-45844c7dd928. Дальнейшие действия записывать ниже до/после переключения.

Исходные URL/CORS и DNS-настройки: VSPOMIN_MIGRATION_PROGRESS_2026-10-10.md и HOSTER_VSPOMIN_DNS_SETUP_2026-10-10.md. Старый Google redirect URI менять/удалять только после добавления нового, готовности DNS/TLS и согласованного изменения PUBLIC_API_URL.

## Контрольная последовательность

1. Добавить api custom domain, записать CNAME/TXT/порт из Railway.
2. Добавить DNS только для api, проверить TLS/health/media.
3. Проверить используемый OAuth client ID против backend (без secret), сохранить старые callbacks; добавить https://api.vspomin.ai/api/v1/auth/google/callback.
4. Переключить PUBLIC_API_URL на https://api.vspomin.ai с контролируемым deployment; проверить фактический redirect_uri выдаваемого /auth/google.
5. Проверить настоящий Google login. После успешного перехода удалить старый callback/domain из Google, сохранив предыдущие значения для восстановления. Не изменять audience/scopes/платежи в этом релизе.
6. Откат: восстановить PUBLIC_API_URL=https://backend-production-e1e8.up.railway.app и старый Google callback/domain, дождаться backend deployment и проверить login. DNS нового домена можно оставить для диагностики.

## Шаг3а — custom domain создан через Railway UI

Добавлен api.vspomin.ai к backend production, порт8080 (uvicorn auto-detected). Старый Railway service-domain сохранён. Configure DNS Records потребовал:

- api CNAME r4rlxw4k.up.railway.app
- _railway-verify.api TXT railway-verify=48e5d852cace3b0a44a132f256a81b07d700fbe54ebf971fecdf952418359994

На этом шаге переменные сервера и callback ещё прежние. Откат без удаления: оставить новый домен неиспользуемым, старый endpoint продолжает работать.

## Шаг3б — API DNS добавлен, переключение ещё не выполнено

В Hoster.by зоне141952 добавлены api CNAME r4rlxw4k.up.railway.app. и _railway-verify.api TXT с выданным Railway значением, TTL3600. Итоговая таблица и прямые запросы u1 подтвердили записи. Снимок artifacts/domain-migration/hoster-api-dns.jpg. Railway UI пока Waiting for DNS update.

Страница конкретного Google OAuth клиента547197616113-bhplutasgos6r5s85g54s3262qrtrl4u.apps.googleusercontent.com не загрузилась: Failed to load; выполнен один Retry. Проверки HTTPS нового API/главной зависли по timeout, отдельное чтение Railway env тоже network timeout. Поэтому PUBLIC_API_URL/Google callbacks/удаление старого domain не выполнялись. Не считать этот этап завершённым удалением Railway из входа.

## Шаг4 — связь восстановлена, подготовлено переключение

После одобрения сертификата пользователем старый и новый API по HTTPS вернули status ok. Client ID backend совпал с клиентом Google. Client name Memorial→vspomin.ai; добавлен новый redirect URI https://api.vspomin.ai/api/v1/auth/google/callback, старый/localhost сохранены на время перехода. Далее планируется изменить только PUBLIC_API_URL; frontend URL/CORS пока прежние.

Откат этого переключения: Railway backend production PUBLIC_API_URL=https://backend-production-e1e8.up.railway.app, затем применить deployment. Старый callback пока зарегистрирован, поэтому возвращение не требует восстановления Google.

## Шаг5 — PUBLIC_API_URL изменён

Google UI подтвердил OAuth client saved. Railway CLI variable set подтвердил PUBLIC_API_URL=https://api.vspomin.ai (set:true). Это запускает применение новых env; deployment и реальный redirect_uri ещё проверяются. Старый API service-domain, старый Google callback, FRONTEND_URL и frontend API пока сохранены.

## Шаг6 — проверено после deployment

10.10.2026 02:32 UTC: deployment 019ec38e-a010-470c-9c5e-2cbece541c02 SUCCESS; предыдущий успешный 374e5b3a-c8da-4689-9407-1ef0a6b6b21e. Новый /api/v1/auth/google возвращает307 с redirect_uri=https://api.vspomin.ai/api/v1/auth/google/callback. В Chrome экран Google «Выберите аккаунт» показывает **vspomin.ai**, без Railway. Снимок artifacts/domain-migration/google-login-vspomin.jpg. Кратковременная502 во время обновления исчезла после успешного deployment/перезагрузки.

Полный вход с выбором аккаунта пока должен завершить владелец; аккаунт за него не выбирался. Поэтому старый Google callback/authorized domain сохранены для немедленного отката. Старый публичный Railway endpoint не удалять: frontend пока использует его. FRONTEND_URL/CORS и база не менялись.

### Точный откат текущего этапа

1. Railway → production → backend → Variables: вернуть PUBLIC_API_URL в https://backend-production-e1e8.up.railway.app, применить обновление и дождаться SUCCESS. Через CLI из связанного проекта: `railway variable set --service backend --environment production PUBLIC_API_URL=https://backend-production-e1e8.up.railway.app --json`.
2. Проверить /api/v1/health/ и /api/v1/auth/google: redirect_uri должен снова указывать на прежний Railway callback. Старый callback и authorized domain уже сохранены в Google, восстанавливать их не нужно.
3. Проверить вход. Новый DNS/API custom domain можно оставить: они не мешают старой схеме. Не удалять сервис, базу или секреты; не откатывать весь проект целиком.
4. Если потребуется откат имени, вернуть App name Memorial (Google Auth Branding) и client name Memorial (Clients); Cloud project display name Memorial в IAM Settings. Project ID/client ID/secret не менять.

После успешного полного входа можно удалить только старый redirect URI и authorized domain из Google; перед удалением сохранить этот журнал. Их значения выше позволяют добавить обратно.

## Шаг7 — frontend домен, 10.10.2026

Владелец подтвердил полный Google login и попросил заменить старый адрес в строке браузера. Railway одним обновлением применяет FRONTEND_URL=https://vspomin.ai/app, PUBLIC_FRONTEND_URL=https://vspomin.ai, CORS_ORIGINS=http://localhost:5173,https://memorial-mvp.vercel.app,https://memorial-mvp-*.vercel.app,https://vspomin.ai. Прежние значения перечислены в VSPOMIN_DOMAIN_AUDIT_2026-10-10.md.

Vercel production VITE_API_URL изменён с https://backend-production-e1e8.up.railway.app/api/v1 на https://api.vspomin.ai/api/v1. Запущена пересборка последнего опубликованного deployment memorial-4is9ag3zb-1alexeikalinin1-3683s-projects.vercel.app (commit12324d3528ba4fefbcdbaf9444b0226b1dc199ee). Текущий dirty checkout не публикуется. Проверка обновления ещё ожидается.

Откат этого этапа: вернуть три Railway env к значениям из аудита одним обновлением; в Vercel вернуть VITE_API_URL на прежний Railway URL и выполнить vercel rollback memorial-4is9ag3zb-1alexeikalinin1-3683s-projects.vercel.app --scope 1alexeikalinin1-3683s-projects. PUBLIC_API_URL можно оставить новым: Google login уже проверен владельцем.
