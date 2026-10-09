# Переезд на vspomin.ai и подготовка закрытого теста

Дата: 9 октября 2026. Домен подтверждён владельцем: **vspomin.ai**. Первые рынки: Беларусь и Россия, далее СНГ. Платёжный провайдер пока не выбран.

## Границы проверки

Проверены исходники фронта и сервера, сборка, маршруты, генераторы ссылок, почта, Google OAuth, Stripe, конфигурации деплоя и документация. Повторная проверка: отдельные поиски старого бренда, старых хостов, `/app`, переменных URL и потребителей этих переменных. Прилагается воспроизводимый перечень совпадений в отслеживаемых текстовых файлах. Секретные .env не копировались.

Это аудит и план, не выполненный переезд. Кабинеты DNS, Google, Vercel, Railway, Resend и платежей, production-переменные, содержимое production-БД и DNS-записи домена не проверены в этой сессии. Их фактические настройки — обязательный следующий этап; отсутствие строки в репозитории не доказывает отсутствие старого адреса в сервисе.

## Схема адресов

Рекомендация: `https://vspomin.ai` — главная, `https://app.vspomin.ai` — приложение без `/app`, `https://api.vspomin.ai` — сервер Railway. `www.vspomin.ai` перенаправляется на основной домен. Пользователь входит на app.vspomin.ai, API callback Google — `https://api.vspomin.ai/api/v1/auth/google/callback`.

Если требуется именно приложение на `vspomin.ai`, а не только главная: приложение собираем в корень; лендинг переносим, например, на `/about`. Сейчас обе части претендуют на корневой index.html. Это отдельный выбор размещения, а не замена DNS. Поддомен `vsponi.ai.app` не является частью купленного `vspomin.ai` и в эту схему не входит.

## Где менять

| Место | Что найдено / действие |
|---|---|
| `frontend/vite.config.js` | Production base `/app/`, output `dist/app`, плагин копирует лендинг в `dist/index.html`. Разделить сборки главной и приложения либо сделать явно управляемые режимы сборки. Локальные изменения файла уже существовали до аудита. |
| `vercel.json`, `frontend/vercel.json` | Две конфигурации rewrites; выяснить фактический Root Directory в Vercel. Для app: корневой SPA fallback; для главной — лендинг. При совместном размещении исключить перехват статики/API. |
| `frontend/src/App.jsx` | Router basename зависит от BASE_URL; проверить все прямые входы после смены base. |
| `frontend/landing/index.html` | Кнопки login/register/demo/тарифов содержат `/app/...`; заменить адресами приложения. Проверить title, description, sharing metadata, canonical, favicon и footer для обоих языков. |
| `frontend/src/pages/Home.jsx` | Две ссылки `Link to="/app/demo"`; заменить маршрутом без дублирования base. |
| `frontend/src/api/client.js` | VITE_API_URL включает `/api/v1`; новая величина `https://api.vspomin.ai/api/v1`, используется и для медиа, и для Google login. |
| `backend/app/config.py`, `backend/.env.example` | Старый Vercel в CORS; сверить PUBLIC_API_URL, FRONTEND_URL, PUBLIC_FRONTEND_URL. Убрать старый пример и синхронизировать документацию. |
| `backend/app/api/auth.py` | GOOGLE callback строится из PUBLIC_API_URL; возврат — FRONTEND_URL. Нужны изменения Google Console и server env одновременно. |
| `backend/app/api/memorials.py:68` | QR helper сам добавляет `/app` для любого production-домена. Сломается даже при корректном новом FRONTEND_URL; убрать эвристику, использовать единую базу приложения. |
| `backend/app/api/invites.py`, `frontend/src/utils/inviteUrl.js` | Backend PUBLIC_FRONTEND_URL и frontend origin+BASE_URL должны выдавать один адрес. Старые приглашения сохраняют токены; старые ссылки требуют redirects. |
| `backend/app/services/email_service.py` | Письма уже vspomin.ai; подтверждение/reset зависят от FRONTEND_URL. EMAIL_FROM уже noreply@vspomin.ai — проверить реальную верификацию в Resend. |
| `backend/app/api/billing.py` | Fallback URLs добавляют `/app` к PUBLIC_FRONTEND_URL: возможен `/app/app`. Убрать добавление вместе со сменой routing; заменить Checkout/webhook/provider. |
| `frontend/src/pages/PricingPage.jsx` | Передаёт success/cancel URL от текущего origin/base; проверить после переезда, согласовать валюту/планы с новым провайдером. |
| `backend/app/api/ai.py`, `backend/app/services/ai_tasks.py` | PUBLIC_API_URL нужен для публичных фото/аудио D-ID/HeyGen; проверить доступ без логина по новому API-домену. |
| `backend/app/api/health.py`, `backend/tests/test_health.py` | service `memorial-mvp` и тест ожидания переименовать согласованно. |
| `backend/app/__init__.py`, package.json, frontend/package.json, e2e/package.json | Проверить описания/package names и lockfiles; npm package name использовать допустимое `vspomin-ai`, публичный бренд — vspomin.ai. |
| `render.yaml`, railway.toml, backend/railway.toml, docker-compose*, start scripts | В render старые имя/URL; выяснить используемые конфигурации. Архивировать устаревший Render только после подтверждения, что он не используется. |
| README, ENVIRONMENT, deploy/start guides, docs, AGENTS, CLAUDE | Обновить актуальную документацию и инструкции; исторические логи хранить как историю, не переписывать факты прошлых деплоев. |
| `frontend/public`, `frontend/landing/video`, artifacts, screenshots | Демо/previews, субтитры, видео и изображения требуют проверки видимого текста; обычный поиск не проверяет надписи внутри картинки или видео. Исключить служебные previews из production. |

## Что означает «заменить memorial»

Старый бренд Memorial MVP / memorial-mvp меняем в пользовательском продукте, метаданных, письмах, именах проектов и актуальной документации. Слова «мемориал» / memorial как название страницы памяти — продуктовая терминология; её изменение требует отдельного редакционного решения.

Не применять глобальный replace к `Memorial`, `memorial_id`, `/api/v1/memorials`, таблице `memorials`, БД `memorial.db`, коллекции Qdrant `memorial-memories` и бакету `memorial-media`. Это действующие идентификаторы и хранилища. Их внешний бренд можно скрыть; если нужно переименовать физически — отдельная миграция с копированием, сверкой и совместимостью. Иначе можно потерять доступ к данным. Уже сохранённые абсолютные ссылки на storage/media проверяем в БД отдельно.

## Внешние сервисы

1. Регистратор/DNS: проверить владельца и доступ, сохранить текущую зону. Добавить записи, которые фактически покажут Vercel и Railway; не использовать выдуманные IP. Сохранить почтовые MX/TXT. Проверить TLS всех трёх адресов.
2. Vercel: добавить главную и app-домен, проверить Root Directory/build/output/env и preview env. Изменения VITE_* требуют новой сборки. Настроить www и redirects старых URL с сохранением пути, query и токенов приглашений. Для старого `/app/*` убирать префикс при переводе на app-домен.
3. Railway: добавить api-домен. PUBLIC_API_URL=`https://api.vspomin.ai`; FRONTEND_URL и PUBLIC_FRONTEND_URL=`https://app.vspomin.ai`; CORS_ORIGINS включает `https://app.vspomin.ai`, `https://vspomin.ai` (лендинг обращается к API), локальные origins — только для dev. Старые origins временно оставить для перехода, затем убрать. Старый API не отключать, пока не проверены внешние callbacks и клиенты.
4. Google Auth Platform: Branding app name `vspomin.ai`, homepage, privacy, terms, support email, Authorized domains `vspomin.ai`; OAuth Client redirect URI — точный новый callback. Проверить consent screen и проверку бренда/домена, а также тестовый/production статус. Screenshot показывает старый хост; точную причину его отображения можно подтвердить только в Console. Подключение домена само по себе не гарантирует смену текста Google.
5. Resend: подтвердить домен, DNS SPF/DKIM по кабинету, настроить DMARC и рабочие support/contact адреса; проверить письма verify/reset в реальном ящике.
6. Supabase/storage/S3: не переносить БД ради домена; проверить bucket URLs, CORS, signed URLs, сохранённые абсолютные ссылки, backups. Supabase Auth redirects нужны только если реально используется Supabase Auth; здесь найдена собственная FastAPI-авторизация.
7. Fish/OpenAI/Qdrant/D-ID/HeyGen/ElevenLabs: сам новый frontend-домен не требует смены API keys; проверить настроенные callbacks, allowlists, публичные URL медиа. Не переименовывать коллекции/клоны автоматически.
8. Платежи: домены checkout возврата, webhook, публичное имя продавца, receipt/support URLs; при смене провайдера потребуется новая интеграция.
9. Отдельно проверить кабинеты аналитики/мониторинга/поисковых систем, GitHub repository links, уведомления CI, social profiles и ссылки в уже разосланных сообщениях. Наличие конкретных интеграций пока не установлено.

## Авторизация: Google, затем Яндекс, Facebook опционально

В текущем Google flow не найден `state`; callback выдаёт JWT через query `?token=...`; связь существующего аккаунта создаётся по совпавшему email без явной проверки `email_verified` у Google. До теста: одноразовый state с привязкой к попытке входа и сроком, безопасный одноразовый код для frontend вместо JWT в URL, валидация профиля и подтверждения email, безопасная политика связывания аккаунтов. Не переносить эти недостатки в новые провайдеры.

Яндекс: зарегистрировать приложение бренда, задать точный `/api/v1/auth/yandex/callback`, секреты только на backend, минимальные права на профиль/email. Ввести таблицу идентичностей `(provider, provider_user_id, user_id)` с уникальностью; production schema migration обязательна — create_all не добавляет столбцы в старую таблицу. Сохранять существующих пользователей и владельцев страниц. Общие routes/callback UI, сообщения ru/en, отмена входа, ошибки, отсутствие email, явное связывание двух методов входа.

Facebook: отдельный этап после Google/Яндекса; предварительно проверить доступность продукта и требования конкретного приложения в Meta Dashboard. Не обещать сроки approval; предусмотреть privacy и инструкцию удаления данных. На старте закрытого теста можно оставить необязательным.

## Замена Stripe для Беларуси и России

Рынок покупателей ещё не определяет доступного провайдера: нужно знать страну, юридический статус и расчётный счёт продавца. Окончательный выбор пока открыт.

Кандидаты для проверки: белорусский эквайринг WEBPAY / bePaid при белорусском получателе; ЮKassa при подходящем получателе и одобрении подключения. ЮKassa имеет процесс подключения нерезидентов, но это не гарантия подключения конкретного белорусского бизнеса. Для bePaid/WEBPAY отдельно получить актуальное подтверждение приёма карт российских банков/Мир, белорусских карт/Белкарт, валют, возвратов, рекуррентных платежей и ограничений банка-эквайера. Архивная новость о поддержке Мир не является подтверждением текущей доступности.

Сравнивать: BYN/RUB и конвертация, фиксированные/процентные комиссии, выплаты, recurring/tokenization, чеки, тестовая среда, договор на цифровой AI-сервис, работа из РФ/РБ. Зафиксировать условия письменно до разработки.

Код: `backend/app/api/billing.py`, config STRIPE_*, `backend/requirements.txt`, `backend/tests/test_billing.py`, `frontend/src/api/client.js`, PricingPage, тарифы лендинга, `docs/MONETIZATION.md`. Сохранить entitlement/квоты отдельно от провайдера. Добавить запись заказа/платежа и уникальный event id, проверку подписи и суммы/валюты/товара, повторные webhook без повторного начисления, delayed payments, refund/cancel/expiry. Тариф активируется по подтверждённому сервером платежу, не по success URL. Если есть живые Stripe-подписки — выяснить их число и согласовать отдельный переход; рекуррентные полномочия не считать переносимыми автоматически. Удалять Stripe SDK/ключи только после завершения перехода.

## Порядок реализации и критерии готовности

1. Зафиксировать размещение приложения и продавца; снять inventory production env/domains/callbacks и резервную копию БД/медиа.
2. Сделать общую генерацию frontend/public URL, исправить `/app` зависимости, разделить сборку и заменить публичный старый бренд. Проверить обе сборки и прямые маршруты.
3. Подключить DNS/TLS, env и Google/Resend; выкатывать согласованно. Старые URL оставить совместимыми. Новый origin не наследует localStorage authToken — пользователи войдут заново; не переносить JWT через redirects.
4. Укрепить OAuth и добавить Яндекс, проверить существующий аккаунт/новый аккаунт/отмену/повтор callback/связывание.
5. После выбора платёжного договора реализовать provider и проверить test платеж, webhook повторы, refund/expiry. Для бесплатного закрытого теста оплату можно скрыть до готовности, не показывать рабочую покупку при неподключённом провайдере.
6. Очистка: инвентаризация tracked/untracked, scripts/seeds, debug routes, локальных artifacts и previews. Удалять только с установленным назначением и резервной копией; uploads/БД/qdrant_storage и пользовательские медиа не считать мусором. Не публиковать данные знакомых/личные образцы в demo.
7. Закрытый тест: реальное ограничение регистрации/доступа, список приглашённых, разграничение owner/family/guest, удаление аккаунта/данных, backups, лимиты затрат AI, журнал ошибок. До теста закрыть выявленную в семейном дереве утечку приватных родственников (см. FAMILY_TREE_AUDIT_2026-10-09.md).
8. Пройти Google/Яндекс, verify/reset email, invite на телефоне, старый и новый QR, public memorial/deep link, media/audio/animation, CORS, checkout/webhook. Проверить Android/iOS, РФ/РБ сети с реальными тестировщиками. Затем наблюдение и план отката env/deployment/DNS; деструктивные schema changes не включать в доменный релиз.

## Официальные источники

- [Vercel: подключение домена](https://vercel.com/docs/domains/working-with-domains/add-a-domain)
- [Railway: собственные домены и DNS](https://docs.railway.com/networking/domains/working-with-domains)
- [Google: проверка бренда](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification)
- [Яндекс ID: регистрация OAuth-приложения](https://yandex.ru/dev/id/doc/ru/register-auth)
- [Resend: проверка и DNS домена](https://resend.com/changelog/domain-claim)
- [ЮKassa: регистрация, включая нерезидентов](https://yookassa.ru/docs/support/merchant/payments/implement/start)
- [ЮKassa: документы и подключение нерезидентов](https://yookassa.ru/docs/support/payments/onboarding/docs)
- [WEBPAY: интернет-эквайринг](https://webpay.by/cards/)

## Приложение: повторный поиск старого бренда и хостов

Ниже — все совпадения в отслеживаемых текстовых файлах для старого имени проекта/бренда, старых Vercel/Railway хостов и dev@memorial.app. Исторические записи также включены для полноты. Это перечень для классификации, не команда заменить каждую строку. Generic memorial identifiers перечислены выше как отдельная миграционная категория.

- `.claude/commands/add-feature.md` — строки 1
- `.claude/commands/bilingual-check.md` — строки 18, 26, 41
- `.claude/commands/check-quotas.md` — строки 1, 14
- `.claude/commands/check-stack.md` — строки 1
- `.claude/commands/debug.md` — строки 1, 9
- `.claude/commands/deploy.md` — строки 1
- `.claude/commands/fix-animation.md` — строки 1
- `.claude/commands/handoff.md` — строки 10, 11
- `.claude/commands/mobile.md` — строки 1
- `.claude/commands/new-endpoint.md` — строки 1
- `.claude/commands/pre-deploy.md` — строки 1
- `.claude/commands/run-tests.md` — строки 12, 31, 75
- `.claude/commands/session-log.md` — строки 1, 4
- `.claude/commands/test-and-fix.md` — строки 8, 9, 10, 126
- `.claude/commands/test-rag.md` — строки 1
- `API_KEYS_GUIDE.md` — строки 170, 243
- `CHECKLIST.md` — строки 51
- `CLAUDE.md` — строки 13
- `DEPLOY_CHECKLIST.md` — строки 5, 15, 22, 33, 34, 50, 53, 62, 67, 121
- `HANDOFF.md` — строки 1
- `QUICK_START.md` — строки 54
- `README.md` — строки 48, 69
- `RUN_LOCAL.md` — строки 73
- `SESSION_LOG.md` — строки 3, 19, 23, 204, 206, 208, 229, 1173
- `SPRINT_0_SUMMARY.md` — строки 7
- `START_GUIDE.md` — строки 8, 23, 39, 54
- `START_INSTRUCTIONS.md` — строки 12, 34, 57, 170, 175, 180
- `STATUS.md` — строки 28
- `TEST_RESULTS.md` — строки 19
- `backend/.env.example` — строки 18, 23, 27
- `backend/app/api/health.py` — строки 14
- `backend/app/config.py` — строки 170
- `backend/app/main.py` — строки 100
- `backend/tests/test_health.py` — строки 17
- `docs/IDEAS.md` — строки 51
- `e2e/package-lock.json` — строки 2, 8
- `frontend/package-lock.json` — строки 2, 8
- `package.json` — строки 2
- `render.yaml` — строки 7, 25, 27
- `start_all.sh` — строки 6
