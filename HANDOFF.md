21.10: запрошены backup/push/deploy перед macOS update. Проверки: backend354passed/9skipped, mobile17integration+15unit/typecheck/lint, frontend14tests/buildpassed. Production templateSECRET_KEY заменён случайным(skipdeploy); после релиза повторныйlogin. Подготовка удалённогоbackup/release идёт, deployment покаНЕподтверждён. SESSION_LOG.md.

20.10 mobileGoogle: кнопка/systemOAuth+PKCEhandoff готовы; отдельный backendmobile_auth+5minDBattempts, прежнийwebcallback сохранён.15unit+17integration/typecheck/lint/doctor20/exports passed; Google synthetic, реальныйiPhoneGoogle ещёНЕпроверен. Нужныbackenddeployment+developmentbuild(ExpoGoнеподходит). ПриоритетiPhone12ProMax, затемiPadAir; QRprep pending. SESSION_LOG.md,mobile/README.md.

20.10 mobile: сохранена локальная веткаcodex/mobile-app; реализована отдельная RN/Expo58 версия вmobile/, общийAPI/аккаунт,13unit+4integration/typecheck/lint/doctor20/builds passed;303web/backendfiles unchanged. Стартовый tagcodex/mobile-start-2026-10-20(commit87736a2). Локальныйsyntheticpreview8081/API8000/web5188; deviceQA/GoogleOAuth/HTTPSlinks ещёpending, production не менялся. Подробностиmobile/README.md,mobile/QA.md,SESSION_LOG.md.

20.10: предложена мобильная IA «Мои страницы/Семья/Профиль», отдельные разделы человека и owner management; утверждённый light/dark логотип встроен в интерактивную концепцию. Гамма одобрена, структура ещё на обсуждении; native app/production не менялись. Preview и проверки — SESSION_LOG.md.

17.10: chat319 вопрос о знакомстве:1504approved/indexed существует; мужской narrator при contributor Alexei Kalinin — возможная неверная атрибуция. Exact liveOpenAI отклонён auto-review, нужно явное согласие на private319→OpenAI; не воспроизведено/не исправлено. SESSION_LOG.md.

16.10: a9cfd70 опубликован,Vercel/RailwaySUCCESS,CI38931683733completed/success(lint-and-test3m45s). Deployed319точный«что ты помнишь о себе?»→биографическийответ/sources1495/1496/1498/suggestFalse. Repairобщийдлявсех,проверкифактовсохранены. SESSION_LOG.md.

16.10: a9cfd70pushed/deployedVercel+Railwaysuccess. DeployedAPI_response319точныйoverview→биографическийответ/sources1495/1496/1498/suggestFalse, defaultpersona/noaudio;HTTP/browserнепроверялся. CI38931683733Run testsпокаидёт;9syntheticlivepassed. SESSION_LOG.md/docs/CHAT_GROUNDED_REPAIR_2026-10-16.md.

16.10: a9cfd70 repairчата pushedmain; VercelD67zt9/Railway60b3ea25pending. Real319exactquestionpatchedprocesssuccess;9syntheticlivepassed. Full351passed+1testassertionfixed/visitor11passed; cloudCIещёожидается. NextdeployedAPI_response319check. SESSION_LOG.md.

16.10: consent319→OpenAIполучен. Live8315bd2overviewошибка воспроизведена: draftфактбезвыбранногоисточника;2specificвопросаsuccess. Local1repair+fullreverifyпрошёлточныйreal319check;9syntheticlivepassed,fullreleaseидёт. ПокаНЕопубликовано. SESSION_LOG.md/docs/CHAT_GROUNDED_REPAIR_2026-10-16.md.

16.10: пользователь сообщает отказchat319наoverview; после1496–1502 проверялось только сохранение. РеальныйHTTPchat ещёНЕзапущен: auto-review отклонилprivate→OpenAI безspecificconsent; требуется разрешение на проверку. Кодoverview уже распознаёт вопрос. SESSION_LOG.md.

16.10: новая жалоба chat319. GitHub main8315bd2/backend+Vercel success подтверждены сейчас;22regressions passed/9live skipped. Текущий ответ на8memories не проверен: auto-review заблокировал private319→OpenAI, отдельное согласие запрошено. Не считать исправленным без воспроизведения; SESSION_LOG.md.

16.10: исправление кириллических имён фото опубликовано8315bd2; Vercel6xg7ciq31sPG6mFLufdatLM9eWfa и Railway1725b926-bdb2-419e-b7bd-36990ce6d5be success. Сайт/API HTTP200. Fullrelease349passed/9skipped; fatalflake8passed. CI38928535316 completed/success (lint-and-test success).

16.10: upload портрета падает из-за кириллицы в Storage key; live synthetic ASCII success/Cyrillic400, cleanup confirmed. Локальный fix UUID.extension +14tests passed; НЕ опубликован. Обход: mama.png. SESSION_LOG.md.

16.10: по рассказу владельца добавлены7approved воспоминаний оСветлане319 (1496–1502), повторное чтение подтвердило8всего;1495сохранена. БезexternalAI/embedding/deploy. SESSION_LOG.md.

16.10 RAG318edbf pushed/deployed Railway2034b839SUCCESS;343tests/45targeted, deployedrealAI3/3answers1494. Cause typoquote mismatch fixed withsourceIDs. Svetlana319memory1495approvedexists, ownerGET200count1; screenshotNetworkError isloadfailure, externalCORScheckpending. Useraskedwhytoolong, finishquickly. docs/MEMORY_EVIDENCE_FIX_2026-10-16.md;SESSION_LOG.md.

16.10 chat319 fix: actual before verifierfalse→aftertrue/source1495; synthetic live9/9 + generationRU/EN2/2,48targeted,346releasefull/348rootfullpassed. Local verifier pronoun/biography/style clarification + private-safe warning, new regressions/doc. e2fa80b deployed: Railway22792559/Vercel4qCa success, livehealth200; CI38922900870 green (lint-and-test3m57s); only ai_tasks/newtest/newdoc committed. Private319HTTP401 without session; exactsource real check before release passed. SESSION_LOG.md.

16.10: по новому исходному фото улучшено сходство, владелец одобрил направление; созданы ещё 3 приватных варианта (нейтральный/окно/сад), не загружены. SESSION_LOG.md.

16.10: chat319 false refusal reproduced with explicit owner OpenAI consent: generator correct, independent verifier false. Local verifier biography/pronoun clarification,30targetedpassed; syntheticRU/EN network timeout, retry pending. No DB writes/deploy. SESSION_LOG.md.

16.10: по семейному видео созданы 3 приватных варианта портрета для выбора владельцем; в мемориал не загружены, код не менялся. Подробности SESSION_LOG.md.

16.10 RAG1494 false-negative reproduced3/3: quote autocorrects typo, exactgate discards goodanswer. Fixed via numbered originalsource segments, realOpenAI after3/3positive;45targetedpassed/fullrunpending. Releaseclone844d213dirtyvoicefiles NOT partofthisfix. Stage onlyai_tasks/newtest/newdoc. docs/MEMORY_EVIDENCE_FIX_2026-10-16.md;SESSION_LOG.md.

16.10: по явному выбору владельца вмемориале319 оставлен новый приватный клон, активнаяTTSмодель s2.1-pro. Прежний клон удалён вFish(APIdelete+GET404 подтверждены) и изmemorial_voices; осталась1готоваяверсия, выбранныйновыйголосдоступен. До удаления проверено, что лишнийvoice_id не используется другими мемориалами/ихбиблиотеками. Другие люди/оригинальные5записей не затронуты. S2Pro/S2.1Pro — вариантысинтеза одного новогоклона; новыйreference_id сохранён. Личныйreceipt selection-and-cleanup-result.txt вприватномкаталогевизуализаций, неGit. Новыхcloning/TTSзапросовнебыло.

16.10 финал:844d213 опубликован; Vercel7120611352success, Railway7120605297success, CI38910685890completed/success. Новыеversionendpoints и UI подтверждены live. Один новый приватный клон из5подготовленныхзаписей создан(state trained), прежний не удалён/не переключён. Новый сохранён вмемориале319 отдельнойreadyверсией2;2готовыхверсии.3реальныеMP3пробы7–9с вприватномкаталоге визуализаций, неGit. Fish production-key доступ кновоймодели проверен перед импортом; сырые воспоминания не читались. Блокировкапубликации снята явнымсогласиемвладельца; повторно спрашивать не нужно.

16.10: владелец явноразрешил production.5f417a4 опубликован(Railway/VercelSUCCESS), savedvoices API/UI live; новыйприватныйклон из5записей создан/добавлен отдельнойверсией, прежнийактивен.3 короткихреальныхMP3/ledgerвприватномкаталогевизуализаций, неGit. CIвыявилнетFFmpeg вrunner;844d213 исправляетCI+503,pushed, новыйCI/deployещёпроверяются. RootHEAD12324d3 сохранён, releasecheckout844d213. docs/VOICE_LIBRARY_2026-10-16.md;SESSION_LOG.md.

16.10: библиотека вариантов голоса +dedup/previewcache/<270s готовы локально;327backend/14frontend/build/browserpassed. Подготовлены5 приватных WAV (3:54) внеGit, оригиналыцелы. Auto-review отклонил commit/push/deploy без явного согласия владельца наproduction; не обходить. Production65c6b52 прежний, чистыйreleasecheckout содержит uncommitted changes. Следующий шаг — разрешение на публикацию. docs/VOICE_LIBRARY_2026-10-16.md;SESSION_LOG.md.

16.10: локальный fix Fish <270s готов,15tests passed; не опубликован. Новый фокус — качество клона мамы через Fish кабинет и подключение voiceID; ждём исходные записи или выбранный voiceID. Production65c6b52. Подробности SESSION_LOG.md.

16.10:65c6b52 pushed/deployed; Railway8671d948SUCCESS, VercelDfp2znskicQJg6kKwBMKsTaq8ocU success/vspomin.ai,CI38820690142green.318backend/14frontend/build, Chromium+WebKit8sizes, guest5/auth15, invitevoice→moderation/author, realRU/ENWhisper, all46signs API passed. Liveguestprivacy/transcribe401/footerpassed. docs/MOBILE_RELEASE_QA_2026-10-16.md +artifacts/mobile-qa-2026-10-16. PhysicaliPhone/mic и newpaidcheckout не проверены; newplans заявки, legacyquotas прежние. RootHEAD12324d3 сохранён, releaseclone65c6b52clean;SESSION_LOG.md.

16.10 mobileQA browser passed Chromium/WebKit8sizes, guest5/auth15, invite voice→pending→approve/author; real syntheticWhisperMP4 passed.318backend/14front/buildpassed. New fixes ready forcommit/deploy, isolated/private/tmp/memorial-moderated-release-20261015; rootHEADunchanged. docs/MOBILE_RELEASE_QA_2026-10-16.md;SESSION_LOG.md.

16.10 verification update: full backend318 passed (122.83s), frontend14 passed, finalbuild passed; browser permission pending, no new deploy.

16.10 mobile/signs/Safari voice QA в работе; новые правки не опубликованы, release /private/tmp/memorial-moderated-release-20261015. 19 targeted backend/14 frontend passed; full backend+повторная build идут. Server/browser запуск twice auto-review timeout, async permission pending; без новых screenshot. Тарифы40/80/140год confirmed, заявки без оплаты. docs/MOBILE_RELEASE_QA_2026-10-16.md; SESSION_LOG.md.

3f01f10 pushed/deployed: Railway5250b364SUCCESS, Verceldpl_4aAFmDEXzQU3jm1G7A77P1FHbft9READY/vspomin.ai,CI38772305865green. LiveguestAPI detail/memories/timeline пусты; newUI/newOpenAPIschemas подтверждены.315+33backend/11frontend/build/browserpassed; syntheticrealOpenAI positive/negativepassed. Private1494 livechat ждёт явного согласия (asyncpending/auto-review), не повторять до ответа. HEADисходногоcheckout12324d3, origin/main3f01f10 (resetотклонён, файлысохранены). docs/MEMORY_AUTHORSHIP_AND_GUEST_FLOW_2026-10-15.md;SESSION_LOG.md.

3f01f10 pushed: authorship/guestprivacy/noanswerCTA,315tests+33targeted+11frontend/build+browserpassed. Synthetic realOpenAI positive/negative passed; private1494 тест требует явного разрешения (asyncpending/auto-review). Новый deploy/CI проверяются. Данные/схема/env не менялись. ИсходныйHEAD12324d3 сохранён после отклонённого reset; git release в/private/tmp/memorial-moderated-release-20261015. docs/MEMORY_AUTHORSHIP_AND_GUEST_FLOW_2026-10-15.md;SESSION_LOG.md.

Push c4aa1d2 выполнен: backend300tests,frontend11/buildpassed; Railwayd104a103 в сборке, Verceldpl_9LPeZqCMTJK1MTkKajhikdasdyUR READY. Ждём backendSUCCESS и live fishing smoke1494. Новые требования авторства/guestprivacy/noanswerCTA подтверждены, не реализованы. ИсходныйHEAD12324d3, origin/mainc4aa1d2: reset отклонён auto-review, только fetch. SESSION_LOG.md.

15.10: воспроизведён и локально исправлен chat после moderation: stale/nonempty vector results скрывали новые approved memories, retrieval exceptions обходили DB fallback. Теперь SQL supplementation18000chars + retrieval fallback, enqueue warning. 36 passed, 98 warnings in 29.52s. Исходный код3failed/1passed. docs/MODERATED_MEMORY_CHAT_FIX_2026-10-15.md; детали SESSION_LOG.md. Без deployment; следующий шаг backend release + live fishing smoke.

Утверждённый frontend опубликован наvspomin.ai: VercelREADY dpl_62azKzWBN1RoXQeZxMZv6EM4wN7K. Новый landing+mobilememorialfixes+usernamehint; live390/images/register/loginпроверены. CLIизолированныйrelease, следующий Git deploy требует docs/VSPOMIN_APPROVED_FRONTEND_RELEASE_2026-10-10.patch. Rollback в одноимённом.md, подробности SESSION_LOG.md.

Аудит приглашений/голоса10.10: anonymous→pending→owner moderation подтверждены,21tests passed. Транскрибация OpenAI whisper-1; найдены anonymous paid endpoint, language mismatch, отсутствие size/format limits и риск Safari MIME/embedding queue. P0/P1: docs/CONTRIBUTION_AUDIT_2026-10-10.md. Реальный микрофон/production Whisper не проверены; код функций и deploy не менялись. Подробности SESSION_LOG.md.

Локально исправлены mobile menuaboveflowers/defaultcandle/uncroppedmedia, явные Delete/Howto labels иusernamehint. Build/browserpassed;34auth tests +forgot/reset UIrealAPI наdisposableDBpassed. Realemail delivery не проверена. Без публикации. Подробности SESSION_LOG.md.

Лендинг локальноv6: compact mobile logo/purpose/CTA, QR overlays устранены, tree top-downSVG, voice available/video soon, новые примеры, signs24h/оформление/approval. Build и1440/390/320 browser passed. http://127.0.0.1:5181/?preview=mobile-v6 . Новых публикаций нет. Подробности SESSION_LOG.md.

vspomin.ai опубликован: старый Vercel адрес →307 на новый, CORS/Google return/QR base/API переключены. Каталог приложения40/80/140 в год и индивидуальный Lifetime; заявки, backend billing/квоты прежние. Мобильный landing: portrait видим, chat под ним, demo CTA убран; Chrome320/build/live assets проверены. Vercel READY dpl_Dn1cJp5qafTFbsP8E6iD1FUP4oj2. Полный rollback и обязательный patch для следующего Git deploy: docs/VSPOMIN_FRONTEND_RELEASE_2026-10-10.md/.patch. Владелец должен повторно войти на новом origin; SESSION_LOG.md.

Исправление свечи12324d3 pushed, VercelREADY. Composition stagez4 выше portraitz3; пересечение со свечой <=25% ширины portrait, resize до границstage(maxscale10). 7backendtests passed, previewv14 DOM25px/100px.

DNS vspomin.ai настроен в Hoster.by: новая зона141952, запрос NS на u1/u2.hoster.by, две @ A-записи Vercel/TTL3600 подтверждены напрямую. Публичная делегация/HTTPS пока не готовы; следующий шаг перепроверить NS и Vercel после распространения. Инструкция docs/HOSTER_VSPOMIN_DNS_SETUP_2026-10-10.md; production env/OAuth не переключались. Подробнее SESSION_LOG.md.

Переезд vspomin.ai начат: домен добавлен в текущий Vercel, DNS invalid (Hoster.by SERVFAIL/REFUSED). Следующий шаг владельца — открыть DNS Hoster.by; точные записи/статус/rollback в docs/VSPOMIN_MIGRATION_PROGRESS_2026-10-10.md. Railway custom domain требует права/reauth. Старые адреса и production env сохранены, /app пока остаётся. Подробнее SESSION_LOG.md.

Опубликовано оформление: 595659a + fix asset routing8681edf, GitHub main pushed. Vercel READY/Railway SUCCESS. /app и атласы HTTP200(image/png), backend/openapi200 и новое полеcomment подтверждены. 12 backend/11frontendtests+build/flake8passed. Черновики landing не включены; интегрирован patch уже действующих тарифов.

Лендинг: privacy2×2/16px/leftalign, pricing heading на общей линии, free banner мягко золотой. Build/mobile проверены. Локально5181, без публикации. Подробности SESSION_LOG.md.

Футер лендинга: логотип290px, отдельная подпись ВАША ПАМЯТЬ НАВСЕГДА на ширину wordmark. Локально localhost:5181, build/mobile проверены. Без публикации. Детали SESSION_LOG.md.

Лендинг обновлён и опубликован 10.10: Plus $40/год, Family $80, Family Pro $140, Lifetime индивидуально; неподтверждённые обещания убраны. Vercel READY dpl_5LiPYWC3zXn9k7sLehZ7wArxvvKc. Биллинг прежний: новые CTA принимают заявки без оплаты. Выпуск только из checkpoint4e87c7c + landing patch; черновики дизайна/редактора не публиковались. Следующий этап — миграция каталога и контроль квот. Аудит docs/LANDING_PRICING_AUDIT_2026-10-10.md; точный patch docs/LANDING_PRICING_RELEASE_2026-10-10.patch нужен перед следующим git-deploy. Подробности SESSION_LOG.md.

Основной тёмный лендинг обновлён локально по уточнению владельца: http://127.0.0.1:5181/?preview=dark-v2. Убраны вымышленные отзывы/цифры/discovery, упрощены инфографика и тарифы, QR-сценарий уточнён; фото Алексей Соколов1947–2021. Build/mobile/RU-EN/FAQ/menu проверены. Без публикации, ждём оценки. Подробности SESSION_LOG.md.

Лендинг: подготовлено отдельное нежное светлое превью frontend/public/landing-gentle-preview.html, открыто на localhost:5180. Desktop/mobile 1440/390/320px и FAQ проверены. Основной сайт не изменён; ждём оценки перед переносом. Аудит docs/LANDING_DESIGN_REVIEW_2026-10-10.md; подробности SESSION_LOG.md.

v13: только выбранный элемент активен; остальные рамки/resize скрыты и pointer/keyboard отключены. Имя/даты z5, выбранный декор z4. Стрелки вынесены в общий верхний слой, tooltip вниз без clipping. Проверено in-app.

v12: нижняя панель оформления — dropdown цветов/свечей; посетители выбирают плитки всех36цветов/10свечей. Каталоги подтверждены in-app, сборка прошла.

v11: добавлен минимальный зазор 28px между именем и фразой на широком экране, включая сохранённые координаты. Browser1240px: фактический зазор63px.

Превью v10: имя/даты всегда z-index5, оформление ниже; стартовая фраза сдвинута вправо, убрана прокрутка фразы. По alpha-bounds всех 36 цветов и 10 свечей рассчитаны индивидуальные смещения центров без изменения PNG. Mobile визуально проверен, build passed.

Исправлен пустой preview v8: standalone bundle требовал JSX automatic runtime. Пересобран с --jsx=automatic, добавлен build:appearance-preview. В браузере v9 подтверждены имя/цветы/фраза и открытие ⋯ → Оформление.

Локальный редактор обновлён: фиксированные стрелки, отдельные цвета, адаптация по ширине шапки, 10 шрифтов/10 свечей/6 цветов по 6 оттенков, комментарии и журнал. Превью v=8. Build, 11 frontend и 12 targeted backend tests passed. Автоматический браузер занят; визуальная проверка новых правок остаётся. Без публикации. Подробности SESSION_LOG.md.

Опубликован4e87c7c, checkpoint-2026-10-09-2305 вGitHub; VercelREADY/RailwaySUCCESS,293backend/11frontendtests. Следующий этап только локальный дизайн: открыто memorial-carnations-preview.html?v=7 сinlineeditor/свечами/цветами идеможурналом. Подробности SESSION_LOG.md и docs/CHECKPOINT_2026-10-09_2305.md.

Контрольная точка по запросу владельца: checkpoint-2026-10-09-2305. 293backend/11frontendtests,build/flake8passed. Текущее состояние подготовлено кpush/deploy; инструкция отката docs/CHECKPOINT_2026-10-09_2305.md. Подробности SESSION_LOG.md.

Локально готов inlineeditor композиции (стрелки/drag/resize/font/size, desktop/mobilelayout), подсказки и API знаков памяти24ч +ownerjournal «⋯ → Знаки памяти». 16backendtests/UIреальныхReactcomponents прошли. Durablepreview memorial-carnations-preview.html используетdemoadapter; app сохраняетнасервер. Production не опубликован. Документ docs/MEMORIAL_APPEARANCE_DESIGN.md; снимки artifacts/memorial-carnations/inline-editor-*.png/signs-journal.png. Подробности SESSION_LOG.md.

Реализовано локально «⋯ → Оформление»: фраза, red/white/none цветы,5свечей/лампадка/фонарь и none; сохранениеpermemorial и public. Центрирование фото в preview/quote исправлены. 13backendtests +6повторно,build/3frontendtests/UIharness прошли. Production не опубликован. Документ docs/MEMORIAL_APPEARANCE_DESIGN.md, снимки artifacts/memorial-carnations/settings-ui*.png. Подробности SESSION_LOG.md.

Первый вариант с гвоздиками выбран. Интерактивное превью свечи/цветов: memorial-carnations-preview.html?v=4; demo24ч, переключение времени, история и сброс. Срок пока предложение; API/production не менялись. Снимки artifacts/memorial-carnations/demo-*.png. Подробности SESSION_LOG.md.

Новое превью с генерированными красными гвоздиками, внешней свечой и ⋯: frontend/public/memorial-carnations-preview.html (3варианта). PNG preview-carnations/red-carnations-v1.png; снимки artifacts/memorial-carnations/. Desktop/mobile проверены; production не менялся, ждём оценку. Подробности SESSION_LOG.md.

Каталог20 разных шапок готов: frontend/public/memorial-compositions-preview.html?v=3 (фильтры/избранное/desktop-mobile/⋯). Mobile190–272px; menus и overflow проверены. Production не менялся; следующий шаг выбор номеров. Снимки artifacts/memorial-compositions/catalog-20-*.png. Подробности SESSION_LOG.md.

Превью композиций шапки уплотнено по замечанию пользователя: крупнее свечи/цветы/альбом, широкие соединённые ветви. Новый снимок artifacts/memorial-compositions/first-hero.png; HTML прежний. Production не менялся. Подробности SESSION_LOG.md.

Логотипы обновлены и опубликованы: e65fd8f, Vercel READY. Горизонтальные на сайте/в шапке/hero, квадратные на auth, light/dark, крупная подпись. Чистый build и11 frontend-тестов OK, live проверено. Основа design/brand; остальные локальные правки не публиковались. Подробнее SESSION_LOG.md.

Логотипы утверждённого набора подключены: горизонтальные для шапки/hero/footer, квадратные для auth, light/dark. Выпуск только логотипов в проверке/публикации. Основа design/brand. Детали SESSION_LOG.md.

Четыре превью композиций шапки: frontend/public/memorial-compositions-preview.html (desktop/mobile), снимки artifacts/memorial-compositions/. В ROADMAP добавлены MEMORY-1–3 (авторские композиции, памятные даты, альбомы с фото/голосом). Ожидается выбор оформления; production не менялся. Подробности SESSION_LOG.md.

Актуальная основа логотипа утверждена и сохранена в design/brand/ (master-reference + листы01–12 + README). Брать за основу этот каталог. Старый PDF от Claude удалён по запросу. Старые генерации остаются архивом; сайт этим действием не менялся. Подробнее SESSION_LOG.md.

Даты создания/редактирования мемориала унифицированы локально: дд.мм.гггг, автоточки, numeric keyboard; проверки дат и frontend build успешны. Для шапки предложен «Свет памяти» со свечами/цветами; без изменений шапки и публикации. Подробности SESSION_LOG.md.

Логотип: текущий raised-wordmark/large-RU принят как основа. Показаны12 превью форматов/палитр по структуре PDF. Ожидается оценка перед сохранением production-набора; сайт без изменений. Пути и детали SESSION_LOG.md.

Логотип: женский профиль отвергнут. Новый preview прежнего знака с поднятым wordmark/крупной кириллицей: design-previews/current-logo-raised-wordmark-large-ru-v1.png. Production без новых изменений; положение V требует оценки. Детали SESSION_LOG.md.

Финальный выпуск 4a45a29 отправлен: Vercel READY/Railway SUCCESS. Везде широкая подпись ВСПОМИНАЙ, light бронза/dark золото; live проверено. 284 backend/11 frontend,build/flake8/PG schema OK. GitHub CI пока in_progress. Женский профиль только preview design-previews/current-logo-feminine-hair-v1.png. Детали SESSION_LOG.md.

Золотой логотип выбран и опубликован на https://memorial-mvp.vercel.app (сайт + app), commit 5297844 локально. GitHub push требует восстановления авторизации. Старые активы/генерации сохранены в design-previews. Русская подпись ВСПОМИНАЙ пока в отдельном превью; последний запрос — на всю ширину vspomin.ai. Детали SESSION_LOG.md.

# Семейное дерево — текущий рабочий этап (2026-10-09)

Локально реализованы боковая панель выбранного человека, поиск/создание родственника, запросы связи между владельцами, защита приватности/циклов, запрос editor и передача владения с принятием получателем. Существующее портретное дерево и ручная расстановка сохранены. 94 backend-теста и8 frontend-тестов прошли, build успешен, два браузерных сценария проверены на отдельной копии демо-базы. Без публикации. Подробности и ограничения: docs/FAMILY_TREE_IMPLEMENTATION_2026-10-09.md и SESSION_LOG.md. Следующий шаг — пользовательский просмотр снимков artifacts/family-tree-review/ и staging-проверка PostgreSQL перед публикацией; модерация споров/полный журнал правок ещё отдельные задачи.

# Handoff — Memorial MVP
> Обновлено: 2026-10-09
> Ветка: main

## Текущий фокус
Аудит доменного переезда подготовлен: docs/VSPOMIN_DOMAIN_MIGRATION_PLAN_2026-10-09.md. Домен vspomin.ai подтверждён, рынки РБ/РФ; следующий шаг — выбрать размещение приложения, проверить production кабинеты и статус продавца для замены Stripe. Изменения продукта не применялись. Подробности SESSION_LOG.md.

Открыто реальное demo-дерево Michael(prod2) в Chrome. Новые3 вида: frontend/public/family-tree-variants.html; явные подписи сына/дочери и раздельные spouse/parent коннекторы, проверено на desktop/mobile. Рекомендация сохранить функции текущего дерева. Подробности docs/FAMILY_TREE_DESIGN_OPTIONS_2026-10-09.md и SESSION_LOG.md.

Семейное дерево проверено: локально43 demo мемориала/152 записи связей,54 теста прошли. Подготовлены два интерактивных вида frontend/public/family-tree-preview.html; изменения продукта ждут выбора. Выявлены утечка приватных родственников через full-tree и отсутствие запрета циклов/конфликтов. Аудит: docs/FAMILY_TREE_AUDIT_2026-10-09.md; подробности SESSION_LOG.md.

Логотип 2 и фонарь 3 применены на главной. Для выбора новой композиции подготовлены три реалистичных семейных альбома с вымышленными AI-фотографиями: /app/album-composition-preview.html (ссылка есть в прежнем hero-composition-preview.html). Цитата/голос центрированы, иллюстративная подпись убрана. Пользователь выбрал первый льняной альбом: применён в Home, вся композиция сдвинута на 30px левее (mobile без сдвига). LemonSlice отложен до оплаты.

## Последнее действие
10.10: рассчитана разовая покупка с200/300 text/month безголоса/видео. Консервативный30yearсценарий: floors$889/$1083, варианты$999/$1199; это30лет, не доказанное вечное покрытие. Details UNIT_ECONOMICS/SESSION_LOG.


Убрана подпись «Озвучка: Fish Audio» в чате локально; frontend build успешен. Пользователю объяснены family checkbox/sync и speech settings по коду. Подробнее SESSION_LOG.md.

S1 убрана локально из Fish UI/API; default и legacy S1 → S2-pro, сохранённая S2.1-pro не меняется. Исправлены два CI ожидания голоса;24 теста и frontend build успешны. Production ещё не обновлён. Подробнее SESSION_LOG.md.

Обработка «Расскажи, что помнишь о себе?» исправлена локально: approved DB memories напрямую, явный overview prompt, строгая проверка фактов сохранена.22 теста прошли; production не обновлён. Подробности SESSION_LOG.md.

Production голос мемориала318 проверен: s2-pro — используется. S1 в CI относится к тестовому мемориалу без выбора; код передаёт сохранённую модель в Fish TTS. Платная генерация не запускалась. Подробнее SESSION_LOG.md.

Лог CI #130 прочитан через авторизованный Chrome: 240 passed, 10 skipped, два падения тестов голоса из-за нового поля model:s1. Причина подтверждена непосредственно GitHub; исправления/re-run не применялись. Подробнее SESSION_LOG.md.

Проверены красные CI #130/#129: падает Run tests, flake8/установка успешны. Локально подтверждены устаревшие ожидания двух тестов голоса (поле model и параметры озвучки); исправления/push не применялись. Детали и ограничения параллельного локального прогона — SESSION_LOG.md.
Выбранный тёплый текст приглашения применён (начало2/концовка1), имя без склонения. Build прошёл,61006b8 отправлен; Vercel production Ready. Подробнее SESSION_LOG.md.

Приглашения: имя без склонения, исправлена повторная пересылка ссылки с /app/, обработка отмены отправки. Восемь invite-тестов и build прошли; c5f91e6 отправлен, Vercel production Ready. Подробнее SESSION_LOG.md.

Исправлен конфликт прокрутки шестого шага туториала при загрузке чата (6ae9374). Build и три layout-теста прошли; Vercel production Ready. Подробнее SESSION_LOG.md.

Туториал опубликован: 30212e7, Vercel Ready. Семь шагов с явными кнопками открытия вкладок «Воспоминания» и «Чат», непрерывным курсором, Назад/прогрессом. Все семь шагов проверены в вебе; три layout-теста и build прошли. Подробнее SESSION_LOG.md.

Настройка голоса переделана в отдельный диалог с четырьмя этапами и закреплёнными кнопками. Опубликовано4fc28c2, Vercel Ready. В вебе проверены центрирование, три модели, текущая S2 Pro, завершение и возврат к чату. Подробнее SESSION_LOG.md.

Мемориал318: девять воспоминаний от третьего лица по биографии владельца заменили прежние, включая неправдивые тестовые море/рыбалку/джаз. Старые векторы удалены. Индексация новых текстов ждёт отдельного разрешения OpenAI. Подробности: SESSION_LOG.md.

Предложена лестница $40/$80/$140 в год без видео, с support/CAC/refunds/setup и налоговым стресс-сценарием. Превью memorial-plan-ladder.html; решения не применены. Последние расчеты в UNIT_ECONOMICS.

Добавлен расчет масштаба без видео для 100/500/1000/10000 paid annual $40 и отдельное интерактивное превью; два usage сценария, fixed сравнения не является прогнозом расходов на рост. Подробности в UNIT_ECONOMICS и SESSION_LOG.

По запросу пользователя удалены все три текущих Fish-клона, привязка голоса/модели мемориала318 очищена. Можно заново загрузить образец и сравнить модели. Детали: SESSION_LOG.md.

Превью экономики $40/год: 100 paid annual при fixed $199.58 и гипотетических variable $0.75 дают $44.25/мес; при variable $3 убыток $180.75. Пользователь отверг $13/$29, цены не менялись. Анализ экономики и предложение тарифов: [UNIT_ECONOMICS_2026-10.md](docs/UNIT_ECONOMICS_2026-10.md). Plus 2 / Family 10 страниц; цены и расходные квоты — гипотезы, текущие тарифы не менялись. Получены расходы владельца: база условно $59.58/мес без API; расчет обновлен. Нужны invoices Fish/OpenAI, страна Stripe и правила private clones без подписки. Lifetime с бесконечным AI требует пересмотра. Подробности: [SESSION_LOG.md](SESSION_LOG.md).

Добавлено клонирование голоса из MP4/MOV/M4V/WEBM: локальное извлечение MP3 через FFmpeg, обновлена проверка и подсказки формы. 6 серверных тестов и frontend build успешны. Опубликовано GitHub→Vercel/Railway (047644d); FFmpeg и MP4→MP3 проверены на production. По запросу пользователя единственный привязанный клон удалён из Fish Audio и БД, все 21 старые аудиоответы удалены из облачного хранилища. Подробности: [SESSION_LOG.md](SESSION_LOG.md).

Текущий новый клон повторно удалён по запросу пользователя перед переклонированием. Добавлены предпрослушивание исходной/очищенной записи и выбор образца, повторное клонирование из файла в текущем окне, темп Fish и словарь произношения. Очистка мягкая, без специализированного детектора вдохов. 10 тестов/build прошли. Опубликовано 04bf12a: Vercel Ready/Railway SUCCESS; очистка синтетического аудио проверена на production (MP3 33061 байт), настройки 0.95× проверены в вебе. Полная загрузка через браузер агента ограничена разрешением расширения на локальные файлы.

Первое лицо в RAG: убрана вводная про сохранённые воспоминания, добавлена проверка перефразирования по точным источникам; отсутствие сведений — «Я не могу найти информацию об этом в моих воспоминаниях». Исходная запись теперь выбрана после очистки по умолчанию. Опубликовано 485d6e2 (Railway SUCCESS, веб Ready); live RAG на вымышленных данных ответил от первого лица и корректно отказал при отсутствии информации. Fish production всё ещё s1, исходник/клон пользователя не прослушаны.

Подготовлено исправление ложного лимита админов в UI и DB-флаг is_admin. Опубликовано 524d654 (Vercel Ready/Railway SUCCESS). Production: аккаунт уже effective_global_admin=True через серверную настройку; chat_limit=None. После уточнения пользователя DB is_admin=True сохранён для его аккаунта. Подготовлены owner-only назначение/отзыв админов и сравнение Fish s1/s2-pro/s2.1-pro с сохранением модели для мемориала; опубликовано 1356cd7 (Vercel Ready, Railway SUCCESS). Пять воспоминаний владельца (318, IDs1487–1491) успешно проиндексированы после явного разрешения передачи в OpenAI. В вебе проверены отсутствие лимита, три кнопки сравнения и owner-only раздел администратора. Подробности: SESSION_LOG.md.

## Следующий шаг
Проверить QR на реальном телефоне и Stripe test-mode webhook/Checkout; live OpenAI grounding уже проверен на вымышленных данных. Новая таблица guest_chat_usage создаётся при старте.

После оплаты LemonSlice проверить подключение photo + streaming Fish voice + existing RAG. Starter на дату проверки: $8/month, 41 included minutes, 3 baseline concurrent sessions, unlimited avatars; стоимость и правила перепроверить перед покупкой. Осталось отдельно live проверить multi-upload/листание нескольких фото. Домены отложены. Окружения: [ENVIRONMENT.md](ENVIRONMENT.md).
