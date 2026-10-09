## 2026-10-09 — Общий выпуск опубликован; корректировка тёмных auth-карточек

Push main b9193cb успешен. Vercel production READY memorial-ekz3as4ol-1alexeikalinin1-3683s-projects.vercel.app; Railway SUCCESS f5ce1d88-fe70-4b97-883b-d69710371e88, оба на b9193cb. Live OpenAPI содержит family requests и ownership routes. В браузере light header подтверждён. Auth-карточки фактически dark: скорректирован BrandVisual пяти страниц на dark вместо light; build успешен, эта небольшая корректировка публикуется отдельным коммитом. Новый женский вариант остаётся preview. GitHub CI общего выпуска ещё идёт.

## 2026-10-09 — Проверки общего выпуска завершены

Полный backend offline-прогон: 284 passed (534.64s); ключи AI/email/storage отключены, DATABASE_URL отдельная tmp SQLite, Qdrant отдельный tmp. Предыдущие ошибки S3 были настройками окружения и не воспроизвелись. Frontend build/11 node-тестов/критический flake8 успешны; локальная PostgreSQL15 проверила создание новых таблиц и повторный запуск schema. Выпуск включает 9365a53,795ee72,e82ff0c и прежний 5297844, всё на main. Старые генерации и новое feminine preview остаются локально. Начинается push/deploy.

## 2026-10-09 — Превью с более явным женским профилем

По дополнительному запросу во время подготовки общего выпуска показана отдельная AI-версия: волосы в виде золотых прядей переходят в линии бесконечности и пиксели, профиль более женский. Сохранено design-previews/current-logo-feminine-hair-v1.png. Надпись/подпись сохранены; новая версия не применяется к production без выбора пользователя.

## 2026-10-09 — Общий выпуск и логотип с подписью на двух фонах

Пользователь явно поручил использовать везде логотип с ВСПОМИНАЙ на всю ширину vspomin.ai, адаптировать светлый фон и push/deploy вместе с остальными готовыми правками. Прозрачные AI-cutout попытки дали артефакты, поэтому сохранён уже чистый production знак/wordmark и добавлена нативная SVG-подпись textLength=1547, x514; никакого изменения формы знака. Light SVG имеет бронзовую цветовую матрицу, тёмный сохраняет тёплое золото. Header light, hero/landing/footer dark; все пять auth-страниц используют полный BrandVisual light. Убран старый brightness-фильтр шапки, сохранено reduced-motion. Браузерное сравнение подтверждено и сохранено design-previews/logo-light-dark-proof.png. Старые версии остаются в design-previews.

В общий выпуск включаются уже подготовленные семейное дерево/уведомления/передача владения, ограничения видимости и циклов, overview воспоминаний, перевод legacy S1 на S2-pro и их тесты. Временная PostgreSQL15 в Docker: создание четырёх новых таблиц и повторный create_all прошли. 11 frontend-тестов, frontend build и критический flake8 прошли. Первый полный backend-прогон с локальной .env упёрся во внешнее S3 (5 cover-photo failures), остановлен; повторяется полностью offline с внешними ключами/хранилищем отключёнными. GitHub авторизация восстановлена пользователем через device flow.

## 2026-10-09 — Золотой логотип опубликован; русская подпись в превью

По явному запросу пользователя выбран current-logo-warm-gold.png. Подготовлен прозрачный вариант current-logo-warm-gold-transparent.png; обновлены brand-flame.svg/static в frontend/src/assets и frontend/landing/images, logo-mark.png для auth. В SVG сохранено лёгкое мерцание двух огоньков и reduced-motion. Прежние активы сохранены в design-previews/brand-before-warm-gold; исходные генерации и все итерации остаются в design-previews/logo-chat-originals.

Коммит 5297844 содержит только 5 активов. GitHub push не прошёл: сохранённый токен аккаунта невалиден. Чистая release-копия /private/tmp/memorial-logo-release собрана успешно. Первый deploy без project link вызвал неоднозначность services, следующую попытку отклонил auto-review. После подтверждения точного проекта prj_B3C7STI6HUELC6SNUARVTdtryxMo и успешного vercel build --prod с полученными настройками повторная проверка одобрила deploy --prebuilt. Production READY dpl_4s72NbGYLHoRnbXDtQqhD5wr1dS8; alias https://memorial-mvp.vercel.app. Публичный images/brand-flame.svg скачан и побайтно совпал с выбранным активом. Build обеих частей сайта успешен. Прочие локальные правки не включены.

Дополнительное превью с подписью ВСПОМИНАЙ: design-previews/current-logo-warm-gold-ru.png. Пользователь попросил растянуть подпись на всю ширину vspomin.ai; отдельная imagegen-правка. Эта подпись пока только превью, в опубликованную версию не включена.

## 2026-10-09 — Текущий логотип проекта в тёплом золоте

Проверены BrandVisual/Layout/Home: используется brand-flame.svg, static sibling brand-flame-static.svg. Статичный SVG отрендерен в design-previews/current-logo-reference.png. Built-in imagegen: edit current lockup using v7 only as warm metallic gold color reference, preserve pixel profile/infinity/wordmark/flames. Превью design-previews/current-logo-warm-gold.png. AI-версия для сравнения, не точная замена SVG; исходные production assets/код не менялись.

## 2026-10-09 — Правое кольцо компактнее, золотая пыль слева убрана

Пользователь одобрил направление v6 и попросил слегка поджать правую петлю влево, убрать шум/золотую пыль слева. Built-in imagegen: compress right lobe horizontally7–9%, preserve vertical size/profile/hair/text spacing/flames; remove all airborne dust around left loop, preserve memory photos above right. Результат design-previews/logo-chat-originals/05-option2-clean-v7.png. Визуально правый край сдвинут влево, фон слева очищен. Превью, сайт без изменений.

## 2026-10-09 — Отступ надписи и уменьшение огоньков

По запросу пользователя built-in imagegen выполнил локальную правку v5: lower wordmark/subtitle, reduce flames to65%, preserve upper mark. Результат design-previews/logo-chat-originals/05-option2-spacing-v6.png: увеличен просвет между огоньками и волосами. Сайт без изменений.

## 2026-10-09 — Небольшое уменьшение правого кольца

По замечанию пользователя правое кольцо v4 чуть больше. Built-in imagegen выполнил тонкую правку: уменьшить внутреннюю область справа примерно6–8%, приподнять нижнюю дугу, сохранить положение головы и прочие элементы. Результат design-previews/logo-chat-originals/05-option2-balanced-v5.png. Это визуальное превью; точное равенство площадей не измерялось. Сайт без изменений.

## 2026-10-09 — Голова вправо и раскрытие правого кольца

По запросу пользователя built-in imagegen отредактировал v3: move head right, enlarge right negative space to match left, hair along outer arcs. Результат design-previews/logo-chat-originals/05-option2-head-right-v4.png. Правая внутренняя область заметно раскрыта; фотографии перенесены над верхней дугой для освобождения кольца. Математическое равенство площадей не проверено; превью для оценки пользователя. Сайт без изменений.

## 2026-10-09 — Нижняя правая дуга варианта2

Пользователь выбрал вариант2 и приложил красную направляющую для углубления нижней правой дуги. Built-in imagegen: change only lower-right gold arc following red guide, preserve profile/hair/upper arcs/left lobe/text; remove annotation. Результат design-previews/logo-chat-originals/05-option2-lower-arc-v3.png. Нижние экстремумы визуально стали ближе, точная геометрия не измерялась. Сайт не менялся, ждём оценки.

## 2026-10-09 — Четыре превью пропорций логотипа №5

По запросу пользователя built-in imagegen подготовил 2×2 comparison board: 1 широкие кольца/малая голова, 2 округлые/средняя, 3 широкие/крупная, 4 компактные/малая. Исходник05, сохранить gold/profile/hair; prompt требует симметричный infinity scaffold до интеграции головы. Файл design-previews/logo-chat-originals/05-four-proportions-preview.png. Геометрическая симметрия генерацией не гарантирована: правая часть остаётся визуально отличной. Предложено выбрать композицию для следующей доработки. Сайт без изменений.

## 2026-10-09 — Доработка выбранного логотипа №5

Пользователь выбрал исходник05: сохранить профиль справа и переход волос в ленты, выровнять пропорции колец. Built-in imagegen выполнил две правки: 05-refined-board-v1.png и крупный 05-refined-mark-v2.png в design-previews/logo-chat-originals/. Prompt: edit original05, equal width/height of infinity lobes, centered crossing, preserve gold/profile/hair/memory particles/wordmark/flames. Визуально приблизили размеры; математическая симметрия не подтверждена и остаточная разница контуров сохраняется. Это preview, сайт не обновлялся. Следующий шаг — оценка пользователем и точная геометрия при финализации.

## 2026-10-09 — Исходные генерации логотипа из ChatGPT

По просьбе пользователя из чата «Идеи логотипа VSPOMIN.AI» (6ac82047-68d8-83ed-8d96-ce10d6a1a0a3) через Chrome и кнопку Скачать получены 10 оригинальных PNG. Сохранены без изменений в design-previews/logo-chat-originals/01.png–10.png; номера соответствуют галерее просмотрщика, хронология не подтверждена. Новая генерация и изменения сайта не выполнялись. Следующий шаг — выбор исходника и конкретных правок пользователем.

## 2026-10-09 — S1 исключена из выбора Fish Audio

По просьбе пользователя после приложенного предупреждения Fish о retirement S1 убрана из UI сравнения, Literal preview/select API допускает только s2-pro/s2.1-pro. Значение по умолчанию в config и .env.example — s2-pro, согласно выбранной пользователем модели. Новый services/voice_models.py согласованно разрешает legacy s1 в сохранённом выборе/серверном env как s2-pro при status и реальном TTS HTTP заголовке; voice_id/reference_id не меняются, сохранённые s2-pro/s2.1-pro сохраняют приоритет. DB не переписывалась, production пока не обновлён.

Обновлены два устаревших CI-теста голосовой анимации: поле model, speed/pronunciations/model аргументы. Новые проверки запрещают выбор/preview S1 и проверяют фактический HTTP model для legacy S1 и сохранение reference_id.24 теста прошли (voice preview, AI mocked, memory overview), frontend build и diff-check успешны. Платные запросы не выполнялись. Commit/push/deploy не выполнялись; параллельные изменения других задач сохранены.

## 2026-10-09 — Исправление общих вопросов к архиву воспоминаний

По запросу «исправь обработку» добавлен services/memory_overview.py: узкое распознавание RU/EN вопросов о себе/жизни, без захвата тематических, текущих или составных запросов. Для overview avatar/chat получает одобренные непустые воспоминания прямо из БД (до30 записей,18k символов с равной долей для каждой), обходя embeddings/indexing/vector search. Конкретные вопросы сохраняют прежнюю RAG-ветку. В generate_rag_response добавлена инструкция для общего рассказа:1–3 подтверждённых биографических факта считаются прямым ответом, без требования буквального «помню». Exact quotes и независимый verifier остаются обязательными.

Добавлен test_memory_overview.py: регистр/пунктуация RU/EN, запрет расширения тематических/current/invention-вопросов,9 approved memories без embeddings, исключение pending, бюджет контекста, принятие/отказ независимого verifier. Проверки:22 passed (новые тесты + test_visitor_flow), компиляция Python и diff-check успешны. Платных OpenAI/Fish запросов не выполнялось. Production не обновлён, commit/push не выполнялись. Существующие параллельные изменения семейного дерева и других модулей сохранены.

## 2026-10-09 — Проверка S2-pro после уточнения о S1 в CI

В production мемориале318 через Chrome открыт диалог настройки голоса: s2-pro — используется. Выбор не менялся, платные preview/чат/загрузка не запускались. S1 в CI — значение по умолчанию для нового тестового мемориала без voice_tts_model. Код сохраняет выбор в Memorial.voice_tts_model; avatar/chat передаёт его generate_speech, Fish TTS ставит выбранную модель в заголовок model, fallback FISH_AUDIO_MODEL применяется при пустом выборе. Создание clone /model отдельно от TTS: запись сохраняется как reference_id, в запросе создания параметра s1/s2-pro нет. Настройка пользователя S2-pro подтверждена интерфейсом; реальный платный запрос Fish не выполнялся.

## 2026-10-09 — Логи CI прочитаны через авторизованный Chrome

После уточнения пользователя о входе в браузере прочитан реальный лог CI #130 (37849572878/job/113558845025) через Chrome. Итог GitHub: 2 failed, 240 passed, 10 skipped, 671 warnings за499.22s. Оба падения — test_voice_reply_starts_video_animation[True/False], лишнее поле model:s1 относительно устаревшего ожидаемого JSON. Ошибка семейных связей из локального параллельного прогона в этом CI отсутствует. Доступ через браузер работает; повторная авторизация CLI для чтения этих логов не нужна. CLI отдельно имеет недействительный сохранённый токен. Изменения тестов, push и повторный запуск не выполнялись.

## 2026-10-09 — Реализация семейного дерева и согласования прав

Пользователь разрешил реализацию согласованного сценария. Сохранены существующее портретное дерево, поколения, линии супругов/бывших супругов, масштаб и ручная расстановка. Добавлены выделение человека и боковая панель, поиск доступных/публичных страниц, быстрый приватный мемориал, похожие страницы, явное направление связи, необязательная связь при обычном создании, защита повтора после частичного сбоя. Живой человек требует подтверждения согласия в обеих формах. Общие родители предлагаются отдельными снятыми флажками, не создаются автоматически.

Между владельцами — отдельные запросы связи с принять/отклонить/отменить, публичность независима от страницы и прав редактирования. Поиск и пять читателей графа фильтруют доступность до обхода, семейный RAG и синхронизация защищены теми же правами. Запрещены циклы/дубли/конфликты поколений. Новые sidecar-таблицы создаются create_all; реальные старые связи без согласия скрываются от посторонних, канонические EN демо сохранены.

Существующие запросы доступа расширены повышением viewer→editor, пояснением родства. Реализованы предложение передачи владения только реальным владельцем, принятие подтверждённым получателем, сохранение прежнему владельцу editor либо отзыв доступа, отмена устаревших запросов связи. Владение и права не выдаются автоматически за родство.

Проверки: 92 backend family/access/workflow + семейный RAG + удаление/повтор публичности =94 прошли; 8 frontend helper-тестов; frontend build и строгий backend flake8 успешны. UI с двумя аккаунтами прошёл поиск→согласие→создание родителей→передача владения, выбор человека и мобильную ширину; отдельно повтор связи после искусственного503 без дубля. Полный CI не заявлен зелёным: ранее выявленные два voice-теста не изменялись. Проверка выполнялась на отдельной копии SQLite `/tmp/vspomin-family-review.db`, не на продакшене или исходной базе. Старые отсутствующие auth-колонки и статус воспоминаний исправлены только в этой временной копии для теста, не в продукте.

Подробные сценарии, API/таблицы, проверки и оставшиеся отдельные этапы: docs/FAMILY_TREE_IMPLEMENTATION_2026-10-09.md. Реализован первый рабочий этап; модерация споров, полный журнал правок/восстановление, email/push, фильтры поиска и серверная дозагрузка графа ещё отдельные задачи. Снимки artifacts/family-tree-review/. Публикация/коммит/push в этой сессии не выполнялись. Прежние изменения других задач сохранены.

## 2026-10-09 — Диагностика красных GitHub Actions CI

По запросу «проверь» проверены GitHub Actions CI #130 (37849572878, 61006b8) и #129. Установка зависимостей и flake8 успешны; падает Run tests (около 8m23s). Детальные логи через GitHub API недоступны текущей авторизации: HTTP403 Must have admin rights to Repository. Аннотации содержат только exit1 и предупреждения, не traceback.

Локально воспроизведены два падения test_ai_mocked.py::test_voice_reply_starts_video_animation[True/False]: ожидаемый JSON tts/status не включает добавленное поле model (s1). Дальнейшее ожидание generate_speech также устарело: реальный вызов передаёт speed, pronunciations, model. Исходники и CI не исправлялись, push/re-run не выполнялись.

Дополнительный полный прогон с временным внешним pytest-plugin, отключающим delay очереди embeddings, и пустыми AI/email-ключами: 249 passed / 3 failed за92.43s. Третье падение test_family_relationships_full.py::TestValidation::test_different_types_between_same_pair_allowed (409 вместо201) относится к одновременно изменявшемуся незакоммиченному backend/app/api/family.py; его нельзя считать причиной опубликованного CI. Два медленных прогона без plugin остановлены после завершения дополнительного полного прогона. CI не поднимает Redis, создание воспоминаний пробует Celery и замедляет тесты. Рекомендация: обновить ожидания тестов голоса и изолировать очередь в тестовом окружении; зелёный GitHub run пока не подтверждён.

## 2026-10-09 — Аудит переезда на vspomin.ai

Подтверждён домен vspomin.ai, первые рынки РБ/РФ, платёжный провайдер не выбран. Подготовлен docs/VSPOMIN_DOMAIN_MIGRATION_PLAN_2026-10-09.md: inventory бренда/хостов, routing /app, frontend/backend URL, QR/invites/mail/media/OAuth/billing, внешние кабинеты, пошаговый переход/rollback и критерии закрытого теста. Повторный поиск tracked text приложен с номерами строк. Найдены QR helper с принудительным /app, billing fallback /app/app, Home /app/demo, Google без state/JWT в query/непроверенное связывание email. Предложены app.vspomin.ai и api.vspomin.ai, отдельная схема root-app при необходимости. БД/коллекции/бакеты не переименовывать глобально. Платёжные кандидаты требуют страны/статуса продавца и актуального подтверждения РБ/РФ способов оплаты. Проверены официальные документы Vercel/Railway/Google/Яндекс/Resend/ЮKassa/WEBPAY. Кабинеты и production env/DNS в этой сессии не проверены; runtime, DNS и платежи не менялись, тесты не запускались (изменена документация). Существующие локальные изменения сохранены.

## 2026-10-09 — Approved warm invitation wording

Applied user-selected invitation opening2 with ending1 to Russian memoryList.invite_sms. Memorial name stays verbatim in quotes, link appended. Frontend production build passed, pushed61006b8; Vercel production Ready, primary alias memorial-mvp.vercel.app confirmed. No recipient messaging or data changes.

## 2026-10-09 — Реальное demo-дерево открыто, три дополнительных варианта

Пользователь отметил, что первое preview не объясняет, чей ребёнок ниже, и попросил открыть существующее дерево и предложить дополнительные оформления с сохранением возможностей.

Через Chrome /app/demo выбрана Kelly, Michael Robert Kelly (production ID2, отличается от локального ID18). Открыта /app/memorials/2?tab=family, загружено21 карточка/граничные ветви, «К этому человеку» приблизила Michael/Catherine/Sarah/Daniel. Tab1256942473 marked deliverable, оставлена пользователю. Fullscreen click не подтвердился переходом в fullscreen; заявляем только открытие/центрирование. Данные/координаты не сохранялись.

Подготовлено frontend/public/family-tree-variants.html (vspomin-design-agent): три вида — классический холст, семейные блоки, слева направо. Explicit Sarah daughter и Daniel son Michael/Catherine; Emily daughter David/Jennifer, spouse Daniel. Родительские линии приходят в карточку ребёнка, супруги соединяются отдельно. Robert/Patricia отмечены бывшими супругами (как actual prod). При визуальной проверке исправлена ошибочная подстановка тётки Patricia Anne1901 вместо матери Patricia Ann Murphy1935–2010; сверено с локальной базой. Zoom/pan/focus/fit/выбор и ветвь родителей Emily, demo wizard existing Daniel/Emily без duplicate; полная интеграция ports/сохранения не выполнялась.

Playwright локально: три вида, explicit son, выбор Sarah→список родителей, zoom, hide branch7nodes, absent search→disabled save, reopen reset, duplicate toast, viewport390 для всех3 без page overflow, no pageerror. Три desktop screenshots обновлены после исправления имени, artifacts/family-tree-review/variant-{1,2,3}.png. Browser security policy запретила открыть file:// нового preview в Chrome: не обходили. Пользователю доступны локальный HTML-link и screenshots; actual online tree открыт успешно.

Обсуждение/рекомендация: docs/FAMILY_TREE_DESIGN_OPTIONS_2026-10-09.md. Сохранить нынешние функции, улучшить читаемый initial focus/подписи/union geometry. Production UI не менялся. Следующий шаг — выбор оформления и интеграция после privacy/cycle fixes из предыдущего аудита.

## 2026-10-09 — Invitation sharing audit and exact memorial name

Checked MemoryList invitation creation, token backend validation/revocation and ContributePage sharing. No external delivery provider: own invite API/database plus Web Share or Clipboard APIs. Removed name declension from invitation text, panel heading and native share title; Russian templates now use memorial quotes so nominative name is grammatical. Found onward sharing omitted Vite /app/ base; reused buildContributeInviteUrl. Handle native-share cancellation without unhandled rejection, show localized error on other failures. Build passed; all eight backend invite tests passed on isolated SQLite (initial test invocation inherited production DB config and failed DNS before tests; reran with explicit in-memory DATABASE_URL). No messages sent to anyone and no production invite/memory data changed. Pushed c5f91e6; Vercel production Ready at memorial-mvp.vercel.app. Actual outbound sharing not exercised; no authorization to message recipients.

## 2026-10-09 — Fix blocked onboarding voice step

User screenshot showed step6 with disabled Next after opening Chat. Found DOM MutationObserver scheduleMeasure cancels the shared animation frame used by initial find/scroll; async chat mounting could prevent target scrolling and leave ready=false indefinitely. Separated initial lookup frame from geometry-update frame and cancel both on cleanup. Three layout tests and production build passed. Pushed6ae9374; Vercel production Ready, alias memorial-mvp.vercel.app. Browser reproduction after this fix not repeated; prior production checks covered the normal path, this patch addresses the async frame cancellation seen on user screenshot.

## 2026-10-09 — Проверка семейного дерева и два превью

Запрос: найти тестовые мемориалы, проверить связывание и поколения, предложить упрощение и два дизайна до решения об изменении продукта.

Найдены 43 EN demo memorials/152 directed relationships в backend/memorial.db и двух копиях. Проверены manifest, обратные связи, отсутствующие endpoints/самосвязи и parent/child поколения при каждом из43 корней: ошибок в найденных демо-данных нет. 54 теста family/manifest прошли с DATABASE_URL=sqlite:// USE_S3=false. Первоначальный запуск с окружением проекта упёрся в DNS Supabase; переключён на независимую in-memory базу.

На отдельной in-memory базе API воспроизведены: анонимный full-tree публичного корня выдаёт имена приватных родственников; цепь предков допускает замыкание цикла (201); parent пара допускает противоречащий child (201). Код также классифицирует произвольные фамилии в Other по demo-конфигурации; форма использует общий select и числовой ID при пустом списке. Исправления продукта не применены: пользователь запросил аудит/предложения и превью до решения.

Дизайн подготовлен vspomin-design-agent: frontend/public/family-tree-preview.html, переключаемые «Тёплое дерево»/«Семейный альбом», настоящая вымышленная Kelly-ветвь James, мастер поиска Patricia→sibling с однозначным предложением и добавлением только в preview. Playwright: desktop screenshot обоих видов, поиск без результата блокирует сохранение, сохранение сестры работает, viewport390 не имеет переполнения страницы, pageerror отсутствуют. Локальный Chromium потребовал стандартного sandbox escalation, auto review разрешил. Скриншоты artifacts/family-tree-review/{generations,album,mobile}.png. Внешний дизайн-проект/DesignSync недоступен.

Подробности и порядок внедрения: docs/FAMILY_TREE_AUDIT_2026-10-09.md. Рабочие базы/production и текущий FamilyTree не менялись; live production end-to-end не проверялся. Следующий шаг: исправить приватность и валидацию, затем общий мастер связей и ветви по графу; согласовать визуальный вариант. Существующие изменения HANDOFF/SESSION_LOG/vite config сохранены.

## 2026-10-09 — Onboarding pointer and geometry

Found cursor unmounted when each step cleared rect, then remounted with no initial position; wrappers used instead of exact buttons; repeated scrollIntoView effect triggered on every rect update. Replaced with portal overlay and persistent pointer (initial=false), actual upload/voice buttons and checkbox pointer anchor. One scroll per step; requestAnimationFrame tracks scroll/resize and ResizeObserver tracks target/card sizes. Tooltip placement uses measured size and viewport bounds. Added Back/progress/Escape/focus containment, keyboard focus restoration, reduced-motion support, unavailable-target fallback and updated bilingual voice-wizard guidance. Three layout tests passed (mobile/desktop/short-screen bounds, placement, checkbox pointer); frontend build passed. Published9faa4ec. Browser traversed all five steps and Back; exact cursor coordinates match upload/invite/checkbox centers. Live test revealed async voice-status replaces anchor and shifts chat header; added child-list MutationObserver, font readiness and ResizeObserver rebinding to current anchor with geometry equality guard in ad18f9d. Verified async replacement on live ad18f9d: cursor matches actual Change button center exactly after voice status loads. User further noted automatic tab switches were easy to miss; added separate navigation steps highlighting Memories tab while still in Media and Chat tab while still in Memories, with explicit Open memories/Open chat buttons. New flow7steps, updated bilingual copy and responsive navigation. Published30212e7, Vercel Ready. Traversed all seven steps on production memorial318: Memories navigation shown while Media remains active, explicit Open memories leads to add-memory guidance; explicit Open chat leads to voice guidance; final checkbox step and Done restore focus to help button and remove overlay. Screenshot /private/tmp/onboarding-navigation.png. No paid API calls/data edits required.

## 2026-10-09 — Guided voice setup

Replaced inline scrolling voice panel with native modal dialog rendered through a portal, outside fixed-height chat. Four stages: recording upload/capture, original vs optional cleanup review, Fish-model comparison, completion. Persistent header/step indicator/footer; main action never scrolls with samples. Existing clone opens sound stage directly; replacement available explicitly. Clone success automatically advances to sound, selected model advances to confirmation, Done returns to chat and enables audio. Native dialog focus containment/Escape handling; close disabled during requests/recording. Retained existing samples and comparison API semantics; no paid Fish generation performed. Frontend build and diff check passed. Published commit a92ddca, Vercel Ready. Browser verified existing clone opens model stage, all three model buttons visible, S2 Pro remains selected, Keep current model opens completion, Done closes modal and enables voice replies. Replacement opens upload stage with Next disabled until a sample exists. Browser revealed global CSS reset overrides dialog positioning; fixed explicit inset/margin-auto and improved preview button contrast in follow-up4fc28c2. Full paid cloning/preview not repeated. Final4fc28c2 deployment Ready; browser confirms centered dialog, all three model buttons and pinned footer visible, selected S2 Pro preserved. Screenshot /private/tmp/voice-wizard.png. Browser session required normal Google reauthentication after deploy.

## 2026-10-08 — Biography replaces inaccurate sample memories

Rewrote memorial318 memories in third person using owner biography. Updated IDs1484,1485,1487–1491 and added1492–1493 (nine total): Novogrudok, school hockey, bass-guitar ensemble, Larisa, Katya1999-10-01, local factory/road organization, roadwork in Russia, respected supervisor/helping colleagues, family travel. Removed invented seaside/fishing/jazz/vinyl and habitual family-dinner stories by replacing their records. Deleted old vectors before updating, cleared embedding IDs to prevent stale facts in RAG. DB operation succeeded, count9. New-text OpenAI indexing awaits explicit consent; prior consent covered five earlier texts.

## 2026-10-08 — Лестница annual тарифов с расширенным учетом расходов

Предложены40/80/140 annual без видео: pages2/10/20, clones2/5/10, text100/300/700, voice5/15/40min(bytecaps). Расчет расширен support/setup/CAC5/paymentreserve6.1%+.30/refunds2%/fixed271.25 incl trademark recovery24months/VAT0or20 stress. At500 peruser profit=.91/2.31/3.57 безVAT либо .36/1.20/1.63 приVAT20. Mixed breakeven141/232. Создан memorial-plan-ladder.html inline, математическая динамика проверена5сценариями. Все неизвестные rates/reserves названы assumptions, не всеобъемлющая гарантия actual costs. UNIT_ECONOMICS обновлен. Production/Stripe не менялись. Next: agree audience budget, verify clone entitlement/charges, enforce all-quota cost caps, actual tax/CAC/support/free traffic.

## 2026-10-08 — Расчет масштаба без видео

По запросу пользователя расчет $40 annual для 100/500/1000/10000 paid: обновлен UNIT_ECONOMICS, создан memorial-growth-no-video.html (inline preview). Fixed199.583 одинаков для сравнения, не прогноз infrastructure at10k; variable .75 и3 сценарные. Low-use результат44.25/1019.58/2238.75/24183.75 monthly; active cost3 дает-180.75/-105.42/-11.25/1683.75. Труд/CAC/tax/free audience/знак отдельно; actual usage не измерен. Динамические вычисления проверены успешно. Тарифы/production не менялись.

## 2026-10-08 — Превью экономики $40/год

По запросу пользователя сделано интерактивное превью memorial-economics.html в директории визуализаций чата: annual price/N/variable/fixed/fee/VAT/CAC/trademark. Предыдущие $13/$29 объяснены как расчет целевой 70% маржи с модельными costs, не минимально возможная цена; пользователь отверг для своего рынка, текущая рабочая гипотеза $40/год и ограниченные AI-квоты. При 100 paid annual, fixed $199.583 и variable $0.75 результат $44.25/мес, при variable $3 — -$180.75. Минимальная цена на 100 в low-use сценарии $34.49; break-even82. Variable $0.75 лишь сценарий, не telemetry. Trademark upfront $1000 превращает годовой $531 остаток в -$469. Документ обновлен. Локальная проверка интерактивной логики: 6 сценариев passed. Production/Stripe/тарифы не менялись. Следующее: измерить costs и обеспечить bytes/tokens/media budgets, уточнить приватные Fish slots без подписки, страна Stripe/налоги/CAC.

## 2026-10-08 — Cleanup before voice retry

User explicitly requested deleting all current clones to free all 10 Fish slots. Deleted three private workspace voices (1da0e30513f14510a41c41dd1d1f376d, b0debdba38df468f8bbc54d8671ccb6f, b9d525c8582e4e5ca91bbd3ec41cf3da) via production Fish API. Cleared memorial318 voice_id, voice_provider and voice_tts_model after successful remote deletion; production remaining_fish_links=0. No recordings or chat audio deleted in this action.

## 2026-10-08 — Уточнены реальные расходы владельца

Railway $5/мес, Vercel free, Fish подписка оплачена $20 (период неизвестен), OpenAI $20/мес плюс ~$10 API balance, домен $350/2 года, план торгового знака $1,000. Обновлен UNIT_ECONOMICS_2026-10.md: база условно $59.58/мес без API, домен $14.58/мес, знак как разовый расход/цель возврата. Fish pay-as-you-go без обязательной API-подписки подтвержден; entitlement private clones и downgrade без подписки не подтверждены, не советуем отменять на предположении. Vercel Hobby non-commercial, платный коммерческий сценарий учтен. Фонд роста ~$300/мес с инструментом разработки/резервом/возвратом знака: при $13/$29 mix70/30 и модельных costs покрывается 24 monthly/30 annual клиентами. Ничего не отменялось/оплачивалось, сообщения support не отправлялись. Следующее: invoices Fish/OpenAI, Stripe country, стоимость фактического API, прочие счета.

## 2026-10-08 — Анализ юнит-экономики и тарифов

По запросу владельца изучены MONETIZATION, billing.py, billing API/config/AI и публичные цены Fish, Supabase, Railway, Vercel, OpenAI, Stripe, LemonSlice, Qdrant, Resend. Подготовлен docs/UNIT_ECONOMICS_2026-10.md: инвентарь расходов, предложение 2 страницы Plus/10 Family, общие семейные AI/storage квоты, расчет переменных расходов, комиссии, break-even, live-пакеты и резерв lifetime. Нынешние lifetime с ежемесячным AI без срока и live-квоты в сессиях признаны рискованными. Предложенные цены — гипотезы: $9/$19 старт либо $13/$29 при целевой 70% марже вклада и полном потреблении модельных квот. Фиксированный $200 — плановый бюджет, не реальный счет; $500 — сценарий чувствительности. Запрошены реальные платежи/страна Stripe/существующие покупатели. Продуктовые тарифы, Stripe и production не менялись. Тесты не нужны для аналитического документа. Следующее: подставить счета, внедрить cost accounting/квоты после согласования модели. Подробности и источники в документе.

## 2026-10-08 — Permanent owner admin, delegation and voice-model comparison

- Following explicit user clarification, set production user 1alexeikalinin1@gmail.com `is_admin=True` in DB. Service owner identity is separately configured through SERVICE_OWNER_EMAIL (default this account), requires verified email, retains global admin rights and cannot be demoted through admin API.
- Only service owner may list/grant/revoke global administrators. Recipients must exist, be active and have verified email. Delegated admins cannot delegate; per-memorial access stays editor/viewer only. Added owner-only management section to Detail → Access, and broadened real-owner helper to allow authenticated global admins (not investor demo visitors).
- One Fish clone can be previewed with same fixed test text and speed1 on s1/s2-pro/s2.1-pro. Preview returns no-store MP3 bytes, no stored response files, no model creation/deletion. User-triggered generation is billed by Fish. Selected model persisted per memorial as voice_tts_model, then honored by subsequent chat; choosing clears browser preview object URLs. Samples retained when closing panel to support retry within same page.
- User explicitly approved sending the five texts to OpenAI. Indexed all memories 1487–1491 successfully into local production Qdrant and saved embedding IDs; production confirms indexed_memories=5.
- Checks: billing/sample/admin suites passed (58 tests), visitor+preview/admin suites passed (14), model-header propagation check passed (admin+preview 4 tests); frontend build passed. Pushed 1356cd7 to main: Vercel Ready, Railway SUCCESS. Production confirms owner_admin=True, can_delegate_admin=True, chat_limit=None. Browser confirms unlimited chat, three comparison buttons and owner-only admin management with service owner listed. Screenshots: /private/tmp/voice-model-comparison.png, /private/tmp/service-admin-access.png. Paid live Fish previews were not generated by agent; preview routing/model headers validated with mocks.

## 2026-10-08 — Admin quota UI and five owner-provided memories

- Added DB `users.is_admin` boolean (default false), startup additive migration, read-only auth response flag; server global-admin helper honors it. Account privilege assignment awaits explicit scope confirmation after automatic approval rejection; no account flag has been changed.
- Billing usage now returns null limits for privileged/demo accounts, fixing front-end false 15-question lock despite server quota bypass. Family RAG toggle honors admin/demo flag. 45 billing tests and frontend build passed; ordinary-user 15-limit check passed separately (46 checks). Published 524d654; Vercel Ready and Railway SUCCESS. Read-only production check: existing email-based global admin is already effective for this account, DB admin flag remains false; chat_limit=None and all five memories present.
- Saved exactly five owner-provided memories in memorial 318, IDs 1487–1491: Novogrudok, youth hockey, roadwork in Russia, daughter Katya born 1999-10-01, beloved wife Larisa/cooking. No extra factual embellishments. Search indexing blocked by automatic approval review pending explicit OpenAI text-transfer consent; local Qdrant verified.
- Fish pricing verified: s1 / s2-pro / s2.1-pro $15 per million UTF-8 bytes; free developer model exists. Runtime remains s1; no model switch or new clone.

## 2026-10-08 — First-person grounded answers and clone quality guidance

- Removed deterministic archive quotation prefix from RAG output. Generation returns short first-person answer plus exact excerpts; excerpt IDs/text checked against retrieved approved memories before an independent LLM entailment/subject-attribution check. Unsupported answers return «Я не могу найти информацию об этом в моих воспоминаниях.» (English equivalent included), including empty-context path.
- Additional verifier incurs one small OpenAI request per supported answer; no extra request for unsupported/excerpt-invalid answers. Validation reduces, but cannot guarantee elimination of, model errors.
- Original recording stays selected after preview cleaning; processing must be explicitly selected after comparison. Added reference guidance (30–60 sec, one speaker, stable style/level, no music/echo). Do not assume processing improves identity; actual user's recording/clone has not been auditioned, so quality cause remains unconfirmed.
- Validation: visitor-flow and audio tests 20 passed, additional reject-added-fact test run separately; frontend build passed. Final visitor suite 11 passed plus voice suite 10 passed (21 checks total). Published ae36a7d + 485d6e2; Railway SUCCESS. Live production LLM test on fictional records returned «Я любил шахматы и собирал старые виниловые пластинки.» with source memory_1 and exact first-person missing-information fallback with no sources. Fish runtime model confirmed s1; no model change or paid Fish clone performed.

## 2026-10-08 — Preview cleaning and speech controls

- Added owner-only `/ai/voice/prepare`: extract video audio, validate duration <=10 min/size <=100MB, mild FFmpeg denoise and gate, normalize level, return MP3 no-store; remove all temporary files on success/error/timeout. No Fish model or provider charge from preparation. Not a specialized breath classifier; loud breaths may remain, quiet speech may be affected.
- Voice panel now plays original and cleaned audio and lets owner choose reference. Samples retained only in browser memory while page remains open for repeat cloning; object URLs revoked on removal/unmount/memorial change. Recreating model is a provider operation, no improvement guarantee; old model replacement behavior retained.
- Chat speech settings: Fish speed .85/.95/1/1.1 and bounded 20-entry pronunciation substitutions in speech text only, paragraph separation between sentences. No guarantee Russian stress is honored. Written RAG answer unchanged.
- Validation: 10 isolated SQLite server tests passed (actual MP4 decoding/clean preview, cleanup on errors, no provider/model creation during preparation, pronunciation boundaries/speed propagation/input bounds). Frontend production build passed.
- Published commit 04bf12a through existing GitHub→Vercel/Railway integration: Vercel Ready and Railway SUCCESS. Production API responds; actual FFmpeg cleaning on production returned valid MP3 (33061 bytes) from synthetic 2-second tone, no paid provider calls. Web speech settings and selection 0.95× verified; screenshot `/private/tmp/voice-cleaning-settings.png`. Browser file-upload extension permission remains unavailable, so full browser upload interaction cannot be verified here without changing that permission.

## 2026-10-08 — Повторное удаление голоса перед новым клонированием

По запросу пользователя удалён новый Fish Audio клон мемориала 318 (2e544394d5f7427d807e804c7451edec) и очищены voice_id/voice_provider. Пользователь спрашивает автоматическое удаление вдохов: текущая подготовка MP4 только извлекает звук, специализированный de-breath ещё не реализован; обычный gate/удаление тишины не обеспечивает распознавание вдохов и может повреждать тихую речь.

## 2026-10-08 — Очистка исходников и аудиоответов

По прямому запросу пользователя удалены все 21 сгенерированные chat_*.mp3 из облачного S3-совместимого хранилища (14709925 байт). Повторный список подтвердил 0 файлов. В uploads/voices и uploads/audio локальных файлов не было. Исходники клонирования уже очищаются автоматически после завершения/ошибки. Галерея медиа не удалялась. Пакетное DeleteObjects хранилище отклонило; использовано успешное индивидуальное delete_object.

## 2026-10-08 — Удаление клона по запросу пользователя

В production-БД был один клон (мемориал 318, Fish Audio). Модель удалена у Fish Audio через backend API-ключ, затем voice_id/voice_provider очищены в БД. Исходные записи и прошлые аудиоответы не удалялись. FFmpeg 7.1.5 подтверждён на Railway; реальный production smoke test искусственного MP4 успешно извлёк MP3 без обращения к Fish Audio. Проверка загрузки файла через Chrome extension ограничена настройкой Allow access to file URLs; обычная форма опубликована и содержит поддержку видео.

## 2026-10-08 — Клонирование голоса из видео

В форме клонирования разрешены MP4/MOV/M4V/WEBM и аудиофайлы. Сервер локально извлекает первую аудиодорожку видео в mono MP3 и передаёт только звук текущему TTS-провайдеру (Fish/ElevenLabs). Добавлен FFmpeg в оба Dockerfile и railpack.json: фактический Railway builder — Railpack, а не Dockerfile. Ограничения: 100МБ/файл, 10мин видео, 120с обработки; пустые, повреждённые и беззвучные видео отклоняются до обращения к провайдеру. Временные видео/аудио удаляются на успехе и ошибках. UI RU/EN объясняет загрузку видео. Шесть тестов с настоящим FFmpeg и mocked-provider endpoint прошли; сборка frontend успешна. Платное клонирование в тестах не выполнялось.

## 2026-10-08 — Open portrait candle and landing flame logos

- Replaced red lantern with exposed wax candle at the marked lower-right portrait edge on owner/public pages, including mobile.
- Landing header/footer reuse existing app flame wordmark; both i dots have candle flames, with static reduced-motion alternative.
- Production build passed; isolated Chrome verified candle placement, hover caption (0px → 12px), and all four landing logo assets load. Commit e7f5296 pushed to main; GitHub auto-deployment published frontend. Production landing returns updated flame assets and app CSS contains open-candle selector; no backend changes. Manual Vercel deploy returned Not authorized, but auto-deploy completed successfully.

## 2026-10-08 — Portrait lamp, family tree sync and publication

- Edit-photo caption appears on hover/focus; touch target remains accessible. Red cemetery lamp matches supplied reference, positioned at lower right of owner/public portrait with reduced-motion support.
- All family-tree responses include selected avatar source and crop settings; tree loads saved avatar portrait and refreshes after selection. Covers remain fallback when no independent avatar is selected.
- Validation: production build; 25 backend tests including portraits, QR visitor flow and grounded AI; isolated mobile Chrome verified 30×56 lamp and contained portrait.
- Published visitor-flow changes together with portraits: d7e2a3f pushed to main via SSH; Vercel production READY (dpl_ADGRoQYxgohkiS4gg4rQ93id67da), Railway backend SUCCESS (9933df9d-f424-4649-a4a1-ddd8d7ce780d) for exact commit. Public frontend /app/m route and backend health returned 200 without Authentication required. Additional family-tree tests: 53 passed. Local tools/configuration and Vite proxy override excluded. Real Stripe payment/webhook remains untested.

## 2026-10-08 — QR/приглашения, модерация, квоты и строгая память

Реализован visitor flow: QR к началу чата, полный мобильный портрет (contain), имя чата без склонения, всегда доступные CTA входа/регистрации с безопасным возвратом в исходный чат, сохранение пятого ответа и немедленная блокировка по месячной квоте. Приглашение разрешает приватный текстовый чат по проверенному токену; вклад приглашённых теперь pending без embeddings до одобрения. Модерация перенесена из Доступ в MemoryList, кнопка со счётчиком, badge вкладки и опрос каждые 30 секунд; после одобрения запись становится общей. Только реальный создатель меняет голос и модерирует (включая защиту voice_id/provider/gender и инвесторского обхода).

Новая guest_chat_usage: 5 успешных ответов на browser+memorial, QR/invite общий лимит, без DEBUG owner shortcut. После регистрации 15/месяц на аккаунт; atomic consumption защищает месячный/гостевой счётчик. /pricing связывает исчерпанную квоту с existing Plus Checkout, сохраняет next, показывает ожидание/отмену/подтверждение. Paid webhook guard + async success event; реальная оплата не проводилась. Локальные Stripe ключ/price/webhook заданы (значения не выводились).

RAG: только approved записи, фильтрация устаревших векторных hits по status+memorial, отключена генерация персоны, системные правила не заменяются persona. Модель выбирает дословные фрагменты в JSON, сервер проверяет цитаты и ID; источники показываются только действительно выбранные. Неизвестные/относительные события получают культурный ответ с предложением добавить воспоминание, без придуманных биографических деталей. Компромисс: ответы звучат как цитаты архива, семантическая релевантность всё ещё зависит от отбора модели.

Проверки: 88 tests QR/invites/access/billing/visitor прошли; после последних защит visitor suite: 10 passed; existing AI mocked suite: 7 passed. Mobile Chrome с mock API: QR top≈5px, пятый ответ сохранён, 15 блокирует сразу, register/login next, оплатный success pending→active, cancel, pending→approved, portrait top/bottom visible. Build проходит. Общий lint содержит прежние ошибки вне задачи; changed-file lint: 0 errors, 4 прежних hook warnings. Исправлен TDZ в monthly-limit UI по browser-check. Детали/границы и следующее действие: [docs/VISITOR_FLOW.md](docs/VISITOR_FLOW.md). Скриншоты artifacts/visitor-flow/. Изменения локальные; production и реальная оплата Stripe не проверены. После явного согласия пользователя live OpenAI проверен на вымышленных данных: известное хобби → точная цитата с source; неизвестный фильм и просьба придумать полёт на Луну → культурный no-data ответ без sources. Вопрос про вчера отклонён локальным temporal guard. Все 4 результата ожидаемые (3 сетевых вызова). Первоначальный auto-review отказ снят явным пользовательским разрешением на вымышленные данные.

## 2026-10-08 — Проверка QR, приглашений и доступа

Проведён аудит текущего кода без изменения поведения. QR локально ведёт на публичную /app/m/:id#chat (dev /m/:id#chat), требует is_public; прежние исправления ещё не опубликованы. Конкретный QR с телефона не проверен: нужен его URL. Приглашение label — подпись, не связь с аккаунтом/родством и не контекст аватара. Добавление воспоминаний принимает invite_token; AvatarChat токен не передаёт, backend chat не принимает его, поэтому приватный чат гостю приглашения недоступен. view_media также не реализован как доступ по токену в странице Contribute. Access — зарегистрированный активный пользователь по email, viewer/editor, управление owner; публикация — флажок в редактировании/создании, либо явная кнопка в QR. Рекомендована отдельная подтверждённая связь пользователя с мемориалом для персонального общения. Тесты запущены с DATABASE_URL=sqlite:///:memory: после ошибки DNS Supabase при обычном запуске; 35 тестов QR/invites/access прошли. Эти тесты не покрывают персонализацию и приватный чат через инвайт.

## 2026-10-08 — Выбран первый альбом, применён в Home

Первый льняной альбом из превью добавлен в основной React Home вместе с фонарём, центрированной цитатой и waveform. Композиция сдвинута 30px влево на desktop, 20px на tablet, без сдвига на mobile. Добавлены RU/EN подписи непосредственно в Home; файлы локализации с чужими изменениями не затронуты. Превью тоже обновлено. Сборка проходит. Локальный Home требует входа; опубликованный интерфейс проверяется через браузер. Посторонние изменения мемориалов/QR не включены в commit.

## 2026-10-08 — Реалистичные варианты семейного альбома

Созданы три новые фотореалистичные композиции открытого альбома: льняной, кожаный и тёмный тканевый. Фотографии содержат вымышленных сгенерированных людей. Новое отдельное превью /app/album-composition-preview.html, ссылка добавлена в прежнее hero-composition-preview.html. Цитата и waveform центрированы под книгой; фонарь слегка перекрывает правый внешний край. Убрана подпись «Иллюстративная композиция». Основной Home не менялся. Сборка успешна; проверка в браузере. Пользователь выбирает вариант.

## 2026-10-08 — Объёмный раскрытый альбом

Переделан album preview: кожаная обложка, слои закрытых страниц снизу, центральный корешок и мягко изогнутые открытые страницы с двумя фото. Остальная композиция сохранена. Preview only.

## 2026-10-08 — Упрощение альбома

По запросу: фото в двух соприкасающихся страницах открытого альбома, без наклона/накладывания; сокращён logo-slogan gap, убрана отдельная подпись Пример фразы (общая demo подпись остаётся), waveform выше, desktop scene410 и stretch для согласования границ. Preview only.

## 2026-10-08 — Вернули лёгкое перекрытие фото фонарём

В album preview фонарь сдвинут обратно влево (right -30px desktop / -10px mobile), лёгкое перекрытие края фото; quote и waveform сохранены.

## 2026-10-08 — Обновлён выбранный Семейный альбом

Preview variant1: quote «Я всегда буду рядом / в ваших воспоминаниях», добавлена статичная waveform с «Его голос. Его история.», lantern сдвинут вправо от фото и текста. Пользователь просит показать, основную Home пока не менять. Подпись demo сохранена.

## 2026-10-08 — Ещё три композиции

hero-composition-preview расширен до шести: сохранены album/archive/generations, добавлены book of life, voice thread, window of memory. Те же logo/slogan, демонстрационные материалы. Главная без изменений до выбора.

## 2026-10-08 — Три композиции hero

Новое /app/hero-composition-preview.html с переключением Album / Personal archive / Generations. Существующие иллюстративные landing photos, письмо/цитата явно примеры, статичная waveform не играет fake audio. Выбранные logo2 и lantern3, одинаковый текст/CTA, ссылка demo. Главная не меняется до выбора. Build passed, чужие frontend изменения не включать.

## 2026-10-08 — Мобильная верстка и QR-переход к чату

Исправлены фиксированная высота мобильной шапки и intrinsic ширина страницы владельца; мобильный public hero переведён в поток, имя не перекрывает портрет. Сообщения прокручиваются внутри chat-messages, без scrollIntoView всей страницы. QR URL и копируемые ссылки согласованы с /app/m/:id#chat (dev /m/:id#chat); публичная страница после загрузки прокручивается к чату. Закрытый мемориал сохраняет защиту: QR endpoint отвечает 409 до публикации; окно QR владельца объясняет последствия и предлагает явно открыть публичный доступ, затем генерирует код. Гостям закрытой страницы показывается понятное локализованное сообщение вместо Authentication required.

Проверки: frontend production build проходит; 4 новых backend теста проходят (URL и гостевой доступ после публикации), 23 существующих access теста также проходят. Browser проверка CSS с тестовым содержимым при 390px: document width=390, hero width=366, шапка не перекрывает контент. При 320px public hero: имя на 20px ниже портрета, переполнения нет. Полный живой сценарий на телефоне не проверен: локальный backend не запущен. Изменения не опубликованы, старые QR-коды не содержат нового #chat; после публикации обновить QR. Посторонний diff vite.config.js сохранён.

## 2026-10-08 — Три размера фонаря в hero

Отдельное /app/lantern-size-preview.html: переключаемые full hero композиции с выбранным логотипом2 и фонарём3; размеры340/400/460px вместо текущих260 (+31/+54/+77%). Главная не меняется до выбора. Статичные SVG при reduced-motion. Пользователь выбирает размер.

## 2026-10-07 — Применены логотип 2 и фонарь 3

Пользователь выбрал mark120% + flame i и бронзовый защитный фонарь. Применены в Layout/Home через BrandVisual и SVG assets, отдельные static SVG при reduced-motion. Главная сохраняет две строки слогана. Build passed. Проверен backend: OpenAI AsyncOpenAI(api_key=settings.OPENAI_API_KEY), Fish Bearer FISH_AUDIO_API_KEY; ChatGPT/Codex subscription в runtime не используется. AI balances не заменяют hosting/DB/storage availability. User vite config excluded.

## 2026-10-07 — Пропорции знака и мемориальные лампадки

По запросу пользователя preview /app/candle-preview.html обновлён: три lockups с одинаковой надписью и размером mark 100/120/140% высоты PNG надписи, оптическое центрирование; flame i сохранены. Три огня заменены на красную кладбищенскую лампадку с колпаком, масляную лампаду и бронзовый защитный фонарь со свечой. Отдельный локальный выбор логотипа и огня. Главная не меняется до выбора. Build passed.

## 2026-10-07 — Новые свечи и эскиз i с огоньками

Пользователь отверг три похожих flicker-профиля. /app/candle-preview.html заменён тремя разными SVG исполнениям: объёмная восковая свеча с подтёками и морфингом пламени; прозрачный стакан с отражением; тонкая свеча на бронзовом основании. Добавлены два эскиза wordmark на тёмном/светлом фоне: исходная форма PNG сохранена, две точки i скрыты и заменены SVG огоньками; точка домена сохранена. Pause и reduced-motion останавливают CSS и SMIL. Главная страница и её логотип не изменены; ожидать выбор. Build passed.

## 2026-10-07 — Логотипы, две строки слогана и превью свечей

Использованы wordmark assets из пользовательского PDF (alpha mask восстановлена), увеличен и усилен контраст логотипа шапки, добавлен wordmark рядом с hero mark (aa79aa6). Затем hero container приведён к 1200px и тем же отступам, что header; удалён левый padding слогана; две строки nowrap, русская вторая строка с точкой. Свеча увеличена до 220×366 desktop, 150×250 mobile, на mobile под слоганом (f397648).

Отдельное публичное превью: https://memorial-mvp.vercel.app/app/candle-preview.html — три CSS/SVG анимации (quiet/living/breath), пауза и локальный выбор. Выбор не меняет homepage; ждать номер пользователя. reduced-motion static. npm build passed; Vercel production Ready. В браузере подтверждены одинаковые x header logo/hero brand/heading, две строки и увеличенная свеча, три разные animationName. Скриншоты /private/tmp/brand-hero-final.png и /private/tmp/candle-three-previews.png. Chrome viewport override не изменил innerWidth, поэтому mobile visual verification не подтверждена. Пользовательский vite proxy 8001 сохранён вне коммитов. LemonSlice отложен.

# Session Log — Memorial MVP

> **Где хранится:** этот файл в корне репозитории — рабочая копия для Cursor/IDE. Дублирующий экземпляр: `~/.claude/projects/-Users-alexei-kalinin-Documents-VibeCoding-memorial-mvp/memory/session_log.md`. Новые записи добавлять **в начало** (после этого блока).

## [2026-10-07] Сохранение состояния; LemonSlice отложен
Пользователь явно попросил push/deploy текущего состояния, а realtime LemonSlice отложить до оплаты подписки. Код frontend/backend уже опубликован ранее; новые изменения — журнал тестового Fish аватара и handoff. Локальная настройка Vite proxy 8001 и пользовательские untracked files исключены из публикации. Повторные проверки production после push далее. Новых генераций и платных подписок не запускать.

## [2026-10-07] Тестовый аватар в Fish и выбор realtime провайдера
По явному запросу пользователя выбранный prepared portrait memorial 318 загружен в Fish workspace 058e095209c7400fa1010f5e02074366. Создан private avatar «Fish Audio Test — vspomin.ai», collection 84f36d094e19bbc9a8fbd3bfed97af7a, portrait asset 78026c3157b443f19cb032abe1972cc3, default voice 2379dd5dab534a6294ac42cc37c6ea88. Короткая TTS реплика (127 credits) task ec62dcbf94b947ed8ef36ab414d153a5. Пользователь подтвердил оценку 12750 credits, 4.701sec, 480P Creatify Aurora; generation 65c852d4356644c588996d20b1fd7f9f успешно завершена за ~3 минуты. Результат 77d5c7fd169b6a46b35c2b0b173e66aa, MP4 640x640, https://fish.audio/app/image-video/history/?g=77d5c7fd169b6a46b35c2b0b173e66aa. Не подключено к приложению/realtime. По первичным источникам LemonSlice accepts photo + streaming TTS (any TTS), Tavus Image-to-Replica supports CVI, HeyGen LiveAvatar website now advertises single-image custom avatar. Предложен LemonSlice для сохранения Fish voice + existing RAG. Не создавали сторонние аккаунты/ключи и не передавали фото этим сервисам.

## [2026-10-07] Публикация редактора и live-проверка
Код b7884a0 push main выполнен. Первый Railway deploy df9bfac1-e502-45e5-85f0-939e143812ba собрался, но healthcheck 30s не прошёл; увеличен таймаут до 120s в обоих railway.toml, commit 18c5862. Повторный deploy 2fcec08f-8afd-454a-b512-8fc1ebb5b580 SUCCESS. Vercel production обновлён автоматически. Chrome Google sign-in повторно успешен. В memorial 318 фото отсутствуют; live проверка проведена на demo memorial 10 с существующим media 37: открыть editor, zoom/rotation/reset, save, reload и восстановленный zoom 1.01; отдельный avatar zoom 1.02/save, повторное открытие показывает reset-follow кнопку; возврат к cover сохранён. Альбом 1 из 1 открывается, Escape закрывает. Оригиналы не менялись. Скриншоты /private/tmp/portrait-editor-production.png и /private/tmp/memory-album-production.png. Multi-file upload и листание нескольких снимков ещё не проверены live; backend tests/source selection покрыты ранее. Генерации Fish video не запускались.

## [2026-10-07] Выбор портретов, кадрирование и личный альбом
По запросу пользователя реализованы PhotoPortraitEditor (выбор из альбома, прямая загрузка, zoom/pan/rotation/reset, круглое preview для memorial), отдельные crop/source metadata в memorial.portrait_settings JSON, защищённый PATCH /memorials/{id}/portraits/{cover|avatar}, derived JPEG rendering. Header/cards/public cover используют crop; chat avatar следует за cover до отдельной настройки, independent avatar можно вернуть к cover. Добавлена additive startup миграция JSON; удаления media очищают ссылки. Оригиналы не перезаписываются. MediaGallery убирает UI оживления/polling, поддерживает multi upload, warm candle photo viewer с arrows/swipe/Escape/focus trap/reduced motion; видео/audio сохраняются. Backend HeyGen сохранён. Проверки: 15 tests passed + исправленный access/deletion test; отдельный portrait suite 3 passed, общая сборка passed, lint новых editor/gallery компонентов passed. Legacy lint ошибок в старых компонентах не исправляли. Production/browser verification далее; Fish видео generation всё ещё не интегрировано.

## [2026-10-07] Стандарт фото — production подтверждён
Коммит 3bcb9b7 push main выполнен. Автоматический Railway deploy 976c2947-0d0b-44d8-bcf9-a60af4c9f35b SUCCESS, Vercel dpl_E8psGALHKA94z1kv7jMCVsNEvDjn Ready/Production. GET референса публичного demo media 37 вернул 200: JPEG RGB 600x600, ICC есть, EXIF нет (без апскейла). Chrome на /app/memorials/10?tab=chat показывает подготовленную картинку. Скриншот /private/tmp/avatar-photo-standard-web.png. Генерацию видео в этой проверке не запускали. Fish video transport остаётся отдельной незавершённой интеграцией.

## [2026-10-07] Автоматический стандарт фото для аватара
По запросу пользователя добавлена provider-neutral подготовка референса: EXIF orientation, sRGB ICC, JPEG quality 92, квадрат до 1024 без увеличения, белые поля вместо автоматического обрезания лиц; EXIF удаляется только из копии. Endpoint /api/v1/media/avatar/{media_id}.jpg читает оригинал локально или из S3/Supabase. Чат показывает эту копию; photo animation и voice chat передают её URL в существующие HeyGen/D-ID. Убрана перезапись больших оригиналов при upload: оптимизация применяется только к производным изображениям. 13 tests passed (image contract + mocked AI); после уточнения ICC дополнительно image tests прошли; frontend build passed. Автоматическое распознавание/выбор лица, ручной crop и проверки резкости пока не реализованы; группы не обрезаются. Fish video backend пока отсутствует: подготовленные JPEG пригодны для будущей загрузки, но фактическую отправку в Fish video не утверждаем. Публикация разрешена ранее пользователем; локальная vite настройка исключается.

## [2026-10-07] Результат production deploy и веб-проверки Fish Audio
Финальный backend deploy ff89ff2e-25b7-4869-9795-3f5ef1b06d70 SUCCESS; Vercel dpl_9s1XwjWEovu7ytubJTsHQm92YXvo READY, alias https://memorial-mvp.vercel.app. Изолированная публикация git archive исключила локальные настройки/секреты. В Chrome под существующей сессией пользователя открыт memorial 318, задан короткий вопрос с включённой озвучкой. Получены текст и аудио, плеер запустился; после финального deploy отображается «Озвучка: Fish Audio», продолжительность 9 секунд. Скриншот /private/tmp/fish-audio-web-proof.png. Голос пользователя заново клонирован во время сессии, сохранён provider fish_audio. Видео не проверено: отсутствует портрет; Fish видео в backend не реализовано. Домены и Google OAuth не менялись. GitHub HTTPS token invalid, device login HTTP 500; существующий SSH GitHub доступ подтверждён, push через SSH.

## [2026-10-07] Fish Audio TTS — исправление fallback и индикатора
После восстановления БД у memorial 318 отсутствовали voice_id/фото. Во время проверки пользователь создал новый Fish Audio клон, сохранение подтверждено БД и Railway. Старый интерфейс всегда запрашивал квоту ElevenLabs; исправлено отображение фактического провайдера через защищённый /ai/tts/status. Fallback без клона теперь использует TTS_PROVIDER=fish_audio; существующие клоны сохраняют своего провайдера. Production TTS_PROVIDER установлен fish_audio. 7 mocked AI tests passed, frontend build passed. Коммит 3acbb67 уже опубликован напрямую на Vercel и Railway; GitHub push заблокирован истёкшим gh токеном, начат повторный вход. Финальный deploy TTS изменений и live smoke test в процессе. Фото у memorial 318 нет, поэтому видео невозможно проверить на нём без загрузки портрета. Домены не изменялись.

## [2026-10-07] Подготовка публикации исправлений видеоответов
Пользователь разрешил push и production deploy перед сменой доменов. Supabase восстановлен: публичный demo endpoint вернул HTTP 200. Исправлены конфликт имён обработчика/сервиса animate_photo и распознавание frontend статуса done. Добавлен regression test Fish voice → animation; 6 mocked AI tests passed, frontend build passed. В публикацию включены ранее подготовленные изменения онбординга и переводов; сторонние настройки агентов и скриншоты исключены. Fish Audio видео через MCP пока исследование, backend интеграции нет; существующий HeyGen/D-ID сохраняется. Домены/OAuth не менялись.

## [2026-10-07] Fish Audio — проверка видеоаватаров и OAuth
**Статус:** исследование выполнено частично; интеграция в приложение и пробная генерация ещё не выполнены.

Пользователь выбрал попробовать Fish Audio как потенциально более дешёвую альтернативу, сохранив HeyGen. Добавлено глобальное MCP-подключение `fish-audio`; пользователь завершил OAuth, CLI подтвердил Successful login. Получен реальный каталог инструментов, включая avatar_audio, estimate_video_generation, generate_video и загрузки. Схемы сохранены без секретов в `docs/integrations/fish-audio-mcp-schema.json`; выводы и следующий эксперимент — `docs/integrations/FISH_AUDIO_AVATARS.md`.

Баланс и цены получить не удалось в текущем активном чате: новые native tools пока не подхвачены; отдельный локальный клиент видит каталог, но вызов требует загруженного чата. Подключение к текущему чату отклонено как `already has an active writer`; текущую работу не прерывали. Нужна перезагрузка подключения/чата для native Fish tools. Платных генераций, загрузок пользовательских медиа и изменений БД не было. HeyGen и код приложения не изменены. Дешевизна и пригодность для продакшена пока не доказаны.

## [2026-09-25] Анимированный онбординг-тур + фикс локального auth/vite-proxy + удаление тестового голоса
**Статус:** завершено

**Что делали:**
1. По запросу пользователя спроектировал и реализовал анимированный тур-гайд по мемориалу: подсветка (spotlight) нужного элемента + анимированный "курсор" (framer-motion) + тултип с текстом, кнопки "Далее/Пропустить/Готово". 5 шагов: загрузка фото (Медиа) → добавить воспоминание (Воспоминания) → пригласить друга (Воспоминания) → клонировать голос (Чат) → чекбокс "Отвечать голосом" (Чат). Тур сам переключает вкладки и поллит DOM (querySelector + offsetParent, до 25 попыток по 150мс), т.к. контент вкладок подгружается асинхронно.
2. Автозапуск тура через 500мс после создания нового мемориала (`MemorialCreate.jsx` передаёт `navigate(..., { state: { justCreated: true } })`), плюс кнопка "?" в шапке карточки мемориала для повторного запуска в любой момент. Прогресс/пропуск сохраняется в `localStorage['vspomin_onboarding_done_v1']`.
3. Переименовал чекбокс в чате: "Генерировать аудио" → **"Отвечать голосом"** (EN: "Answer with voice") — `frontend/src/locales/{ru,en}.js`, ключ `chat.audio_label`.
4. Добавил `data-tour="..."` атрибуты-хуки в `MediaGallery.jsx`, `MemoryList.jsx`, `AvatarChat.jsx` для таргетинга тура.
5. Удалил старую клонированную Fish Audio voice-модель у тестового мемориала "Fish Audio Test" (id=318, `voice_id=f88a4f2bb24e490a9770a340f60b3c20`) через `delete_custom_voice()` — освободил слот для записи голоса вживую через кнопку записи.
6. При проверке в браузере обнаружил, что локальный логин был полностью сломан (404 на всех API-запросах) — не связано с самим туром.

**Проблемы и решения:**
- **404 на `/api/v1/auth/login` и вообще все API-запросы.** Причина: `frontend/vite.config.js` проксировал `/api` на `http://localhost:8000`, а там висит посторонний Docker-контейнер (`com.docke...`, порт назван `irdmi`), не связанный с проектом. Реальный backend (со всеми auth-роутами) был поднят на портах **8001** и **8010** (два дублирующих uvicorn-процесса, PID 57711 и 40842 — не мои, не трогал, стоит разобраться отдельно). Фикс: сменил target на `localhost:8001`, перезапустил frontend dev-сервер (vite.config.js не хот-релоадится).
- **После фикса прокси — "Неверный email/пароль".** Сохранённый в Chrome автозаполненный пароль для `1alexeikalinin1@gmail.com` не подошёл. Спросил пользователя явно (AskUserQuestion) — выбрал сброс пароля тестового аккаунта. Сбросил напрямую в БД через `hash_password()` на `Vspomin2026Test!` (сообщено пользователю). Важно: локальный dev подключён к **той же продакшен Supabase Postgres**, что и прод (см. `backend/.env` → `DATABASE_URL`), это реальный аккаунт пользователя, не изолированная тестовая БД.
- **Курсор тура визуально "прыгал" в угол экрана на первом рендере / сразу после смены шага**, пока `querySelector` ещё не находил целевой элемент на новой вкладке — ожидаемо, т.к. компонент рендерит курсор только когда `rect` не null; в момент между шагами он на секунду пропадает/переставляется. Не баг, а следствие асинхронной подгрузки вкладок — визуально не мешает, при живой проверке в браузере все 5 шагов подсветили правильные элементы.

**Проверка:** прогнал весь тур вживую в Chrome (claude-in-chrome) на мемориале id=318, все 5 шагов — подсветка, тексты, переключение вкладок, кнопки Далее/Готово — отработали корректно. ESLint не добавил новых ошибок (только уже существовавшие в проекте `no-empty`/unescaped-entities предупреждения).

**Изменённые файлы:**
`frontend/src/components/OnboardingTour.jsx` (новый), `frontend/src/components/OnboardingTour.css` (новый), `frontend/src/pages/MemorialDetail.jsx`, `frontend/src/pages/MemorialCreate.jsx`, `frontend/src/components/MediaGallery.jsx`, `frontend/src/components/MemoryList.jsx`, `frontend/src/components/AvatarChat.jsx`, `frontend/src/locales/ru.js`, `frontend/src/locales/en.js`, `frontend/vite.config.js`.

**Осталось сделать:**
- Разобраться с двумя дублирующими backend-процессами (8001/8010) — оставить один канонический на постоянно свободном порту.
- Проверить EN-версию тура и текста вживую (переводы добавлены, но не открывал глазами).
- Закоммитить изменения (не коммитил без явного запроса).

## [2026-06-24] Точечный security-аудит: JWT + RAG prompt injection
**Статус:** завершено ✅ (фиксы не закоммичены)

**Что делали:**
1. Изучили внешний репозиторий `mukul975/Anthropic-Cybersecurity-Skills` (817 skills для security ops) — признали избыточным для проекта целиком, но выбрали 2 точно релевантных: `testing-jwt-token-security` и `testing-prompt-injection-in-rag-pipelines`, скачали в `.claude/skills/`.
2. Прогнали `/security-review` — диффа кода не было, перешли к ручному статическому аудиту по чек-листам новых скиллов.
3. Нашли и исправили 4 риска (см. ниже). Часть находок субагента перепроверили руками и одну отбросили как false positive (invite-токены на самом деле жёстко скоплены по `memorial_id`, утечки нет).

**Проблемы и решения:**
- **Дефолтный SECRET_KEY в проде** (`config.py:21` — `"dev-secret-key-change-in-production"` как fallback). Решение: `model_validator` в `Settings` — падает при старте, если `DEBUG=false` и `SECRET_KEY` остался дефолтным.
- **RAG prompt injection** (`ai_tasks.py` — memory.content интерполировался в промпт без разделителей). Решение: явные маркеры `===BEGIN/END MEMORY DATA===` + системный промпт с инструкцией не выполнять команды из данных + функция `_sanitize_memory_text()` (regex, нейтрализует фразы типа "ignore previous instructions" / "игнорируй инструкции" оборачиванием в кавычки, не вырезая текст).
- **JWT не отзывался при смене пароля** (старый токен валиден все 7 дней после password reset). Решение: новая колонка `User.tokens_invalid_before` + `iat` в JWT (`auth.py: create_access_token`) + проверка в `_get_user_from_token` + установка в `confirm_password_reset`. Краевой случай: `iat` хранится как целые секунды, `tokens_invalid_before` — с микросекундами → токен, выпущенный в ту же секунду, ложно отклонялся. Исправлено округлением порога вниз до секунды (`invalid_before.replace(microsecond=0)`).
- **Cross-memorial утечка через `sync_family_memories`** — `memory.content` шёл в промпт GPT-анализа без санитизации, а сгенерированный `reflected_text` сохранялся в ЧУЖОЙ мемориал и показывался в UI напрямую, минуя защиту чата. Решение: `_sanitize_memory_text()` применена и на входе (memory.content), и на выходе (reflected_text).

**Изменённые файлы:**
`backend/app/config.py`, `backend/app/auth.py`, `backend/app/api/auth.py`, `backend/app/models.py`, `backend/app/main.py`, `backend/app/services/ai_tasks.py`, `docs/IDEAS.md` (добавлена SECURITY-3 deferred), `.claude/skills/testing-jwt-token-security/`, `.claude/skills/testing-prompt-injection-in-rag-pipelines/` (новые)

**Тесты:** ast.parse на все изменённые файлы + ручные integration-тесты ревокации JWT на SQLite (issue → reset → старый токен отклонён, новый принят, включая edge case с округлением секунд) — все прошли.

**Осталось сделать:**
- Закоммитить фиксы (сейчас uncommitted).
- `/code-review ultra` — широкий аудит всей кодовой базы перед продом (медиа, Stripe webhooks, CORS/rate-limiting, SQL во всех эндпоинтах, фронтенд). Сохранено как `deferred` в `docs/IDEAS.md` → SECURITY-3.
- Не реализовано (сознательно, низкий приоритет): logout-эндпоинта нет вообще (ревокация при logout не нужна без него); guardrails на выход LLM против утечки фактов другого мемориала при `include_family_memories=true`.

---

## [2026-05-23] Family RAG — ограничение по тарифу + вирусный шеринг баг
**Статус:** завершено ✅

**Что делали:**
1. Viral share в ContributePage: анонимный пользователь пытался создать новый инвайт (401). Фикс: делится той же ссылкой, по которой зашёл.
2. Family RAG guard: бэкенд правильно возвращает 402. Фронт показывал тоггл всем и глушил ошибку.

**Изменения (Family RAG):**
- `AvatarChat.jsx` — `hasFamilyRag` computed: `subscription_plan` в `['plus','pro','lifetime_pro']`
- Тоггл для Free: `disabled + opacity:0.5 + cursor:not-allowed + бейдж "Plus"`
- При 402 в чате: сбрасывает тоггл + показывает upgrade prompt (не ломаный `detail`)
- `AvatarChat.css` — `.feature-locked` + `.plan-badge` стили
- `locales/en.js` + `locales/ru.js` — 2 новых ключа: `family_locked_tooltip`, `family_upgrade_prompt`

**Изменения (viral share):**
- `ContributePage.jsx` — `handleViralShare` теперь использует `window.location.origin + /contribute/:token` вместо `invitesAPI.create()`

**Билд:** ✅ без ошибок

## [2026-05-23] Тесты email-верификации + фикс timezone-бага, все тесты 209/209 ✅
**Статус:** завершено ✅

**Что делали:**
1. Написан `tests/test_auth_email.py` — 22 теста для 4 новых auth endpoint'ов
2. Обнаружен и исправлен production-баг: SQLite возвращает naive datetime, endpoint сравнивал с `datetime.now(timezone.utc)` → `TypeError: can't compare offset-naive and offset-aware datetimes`
3. Фикс в `backend/app/api/auth.py`: нормализация tzinfo перед сравнением в `verify_email` и `confirm_password_reset`

**Изменённые файлы:**
- `backend/tests/test_auth_email.py` — новый файл, 22 теста
- `backend/app/api/auth.py` — timezone-safe сравнение в `verify_email` и `confirm_password_reset`

**Тест-покрытие:**
- `POST /auth/verify-email` — valid/invalid/expired/already-verified токен
- `POST /auth/resend-verification` — auth required / already verified / token обновляется
- `POST /auth/password-reset` — известный email / неизвестный (всегда 200) / срок токена
- `POST /auth/password-reset/confirm` — valid / invalid / expired / one-time use / new password works / old password rejected
- Full-flow: register → verify → /me | register → reset → login

**Итог:** 209/209 тестов ✅

## [2026-05-23] Supabase миграция — email verification + password reset
**Статус:** завершено ✅
**Что делали:** Применена SQL-миграция на Supabase (prod DB).
**Результат:** 5 колонок добавлены в таблицу `users`:
- `email_verified` BOOLEAN NOT NULL DEFAULT false
- `verification_token` VARCHAR(64)
- `verification_token_expires` TIMESTAMPTZ
- `password_reset_token` VARCHAR(64)
- `password_reset_token_expires` TIMESTAMPTZ
- Индексы по токенам созданы.
**Осталось:**
- ⏳ `RESEND_API_KEY` — настроить на проде (Vercel/Railway env vars) — ОТЛОЖЕНО
- ⏳ Написать тесты для auth endpoint'ов — ОТЛОЖЕНО

## [2026-05-23] Email верификация + сброс пароля (Resend)
**Статус:** завершено, тесты 187/187 ✅

**Что делали:**
1. Аудит готовности к проду: 5.5/10 — написана сводная таблица (что работает / что планировалось / что скрыть)
2. Сохранён расширенный бэклог нереализованного в `docs/IDEAS.md`
3. Реализована email-верификация + сброс пароля (провайдер: Resend)

**Backend изменения:**
- `models.py` — добавлены поля `email_verified`, `verification_token`, `verification_token_expires`, `password_reset_token`, `password_reset_token_expires` в `User`
- `config.py` — добавлены `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME`
- `services/email_service.py` — новый файл: HTML-шаблоны писем + отправка через Resend SDK
- `schemas.py` — `UserResponse` +`email_verified`; новые схемы `PasswordResetRequest`, `PasswordResetConfirm`
- `api/auth.py` — 4 новых endpoint: `POST /verify-email`, `POST /resend-verification`, `POST /password-reset`, `POST /password-reset/confirm`; регистрация теперь отправляет письмо верификации
- `requirements.txt` — добавлен `resend==2.10.0`
- `.env.example` — задокументированы новые env-переменные

**Frontend изменения:**
- `api/client.js` — 4 новых метода в `authAPI`
- `pages/VerifyEmailPage.jsx` — новая страница `/verify-email?token=...`
- `pages/ForgotPasswordPage.jsx` — новая страница `/forgot-password`
- `pages/ResetPasswordPage.jsx` — новая страница `/reset-password?token=...`
- `pages/AuthPage.css` — дополнен классами для новых страниц
- `pages/LoginPage.jsx` — ссылка "Forgot password?" + баннер успешного сброса
- `components/VerificationBanner.jsx` — мягкий баннер (не блокирует) для не-верифицированных юзеров
- `components/VerificationBanner.css` — стили баннера
- `components/Layout.jsx` — встроен `VerificationBanner`
- `App.jsx` — 3 новых маршрута: `/verify-email`, `/forgot-password`, `/reset-password`

**Поведение:**
- Регистрация → письмо уходит (если `RESEND_API_KEY` задан). Если нет — токен логируется в консоль (dev mode)
- Баннер показывается только авторизованным, не-demo юзерам с `email_verified=false`. Dismissable.
- Google OAuth → `email_verified=True` автоматически
- Сброс пароля всегда возвращает 200 (защита от перебора)
- Токены: верификация 24ч, сброс пароля 1ч

**Для активации на проде:**
1. Завести аккаунт на resend.com, получить API ключ
2. Верифицировать домен (или использовать `onboarding@resend.dev` для тестов)
3. Добавить в `.env`: `RESEND_API_KEY=re_xxx`, `EMAIL_FROM=noreply@vspomin.ai`
4. Выполнить SQL-миграцию на Supabase (см. ниже в Критический контекст)

**Миграция Supabase:**
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token_expires TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_users_verification_token ON users(verification_token);
CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users(password_reset_token);
```

**Осталось сделать:**
- Запустить Supabase миграцию перед деплоем
- Настроить `RESEND_API_KEY` в Vercel/Railway env vars
- Написать тесты для новых auth endpoint'ов

## [2026-05-23] 404 + Error Boundary
**Статус:** завершено ✅
**Изменённые файлы:**
- `frontend/src/pages/NotFoundPage.jsx` + `.css` — кастомная 404 с кнопками "← Go back" и "Home"
- `frontend/src/components/ErrorBoundary.jsx` — React class component, перехватывает render-ошибки
- `frontend/src/App.jsx` — `<Route path="*">` + `<ErrorBoundary>` обёртка
**Билд:** ✅ без ошибок

## [2026-05-23] Аудит готовности к проду
**Статус:** завершено (анализ)
**Что делали:** Полный анализ проекта — 5.5/10, таблица работающего/нереализованного, ранжирование фич по приоритету скрытия. Результат сохранён в `docs/IDEAS.md`.

## [2026-05-18] Полный аудит: тесты + бэклог + план
**Статус:** завершено

**Что делали:**
1. Запущены все pytest: 177/177 ✅ — ни одного падения
2. E2E: SKIPPED (backend + frontend не запущены)
3. Проверен hardcode owner_id=1: не осталось — JWT auth везде
4. Прочитаны IDEAS.md + ROADMAP.md — полный бэклог
5. Составлен план дальнейшей реализации

**Проблемы:**
- Багов не найдено, все тесты зелёные
- E2E не запускались (offline)
- Много deferred/planned фич которые не начинались

## [2026-05-02] Demo tutorial — 5-шаговый онбординг
**Статус:** завершено, запушено

**Что делали:**
1. Реализован `DemoTutorial` компонент (overlay + hint, шаги 1–5) — `frontend/src/components/DemoTutorial.jsx` + `.css`
2. Шаги 1–2 встроены в `DemoPage.jsx`: step 1 = overlay при первом визите, step 2 = hint после клика на семью
3. Шаги 3–5 встроены в `MemorialPublic.jsx`: переход через `?demo_step=3` в URL, step 3 = hint над чатом, step 4 = hint при переходе на Memories, step 5 = следующий hint там же
4. Прогресс сохраняется в `localStorage` (ключ `demo_tutorial_v1`)
5. E2E тест `tutorial_audit.spec.js` — 7/7 прошли со скриншотами

**Проблемы и решения:**
- CRITICAL: overlay был невидим (белый текст на белом фоне) — `:root { --surface: #FFFFFF }`, `--text-primary` не определён → fallback `#fff`. Фикс: явные цвета `#1e1c19` / `#fff` в CSS вместо переменных
- Step 3 hint уходил ниже вьюпорта (AvatarChat загружается и скроллит страницу) → добавлен `scrollIntoView` через `useEffect` в компоненте
- Step 5 содержал "ask Sean about his great-grandchildren" — имя хардкодом → заменено на нейтральное
- Тест "No tutorial when already done": `context.addInitScript` в `beforeEach` перебивал `page.evaluate` при reload → фикс: `page.addInitScript` выполняется ПОСЛЕ context-скрипта

**Изменённые файлы:**
- `frontend/src/components/DemoTutorial.jsx` — новый (с `useRef` + `scrollIntoView`)
- `frontend/src/components/DemoTutorial.css` — новый (explicit dark colors)
- `frontend/src/pages/DemoPage.jsx` — шаги 1–2
- `frontend/src/pages/MemorialPublic.jsx` — шаги 3–5, `useSearchParams`
- `e2e/tests/tutorial_audit.spec.js` — новый (7 тестов)

**Коммиты:**
- `5a8553b feat: demo tutorial — 5-step onboarding across DemoPage and MemorialPublic`
- `a59e641 fix: tutorial CSS colors explicit + step 3 scroll + step 5 generic text`

**Состояние БД (production-like):**
- 10 пользователей: 2 живых (verameeva77@mail.ru, onemmanwarrior@gmail.com, оба free, 0 мемориалов)
- ID=1 admin@memorial.app — демо-аккаунт (is_demo=True), 43 мемориала
- ID=9 1alexeikalinin1@gmail.com — аккаунт разработчика

**Осталось сделать:**
- E2E тесты с живым стеком (полный прогон)
- Полный регресс pytest (192 теста)

## [2026-04-23] Тесты биллинга и управления доступом — 67/67
**Статус:** завершено

**Что делали:**
1. Аудит покрытия тестами: обнаружили что conftest._bypass_billing глобально отключает все billing-проверки → 0 тестов биллинга
2. Создан `tests/test_billing.py` (44 теста): unit-тесты billing.py с mock User/DB
   - `_effective_plan`: free, expired plus→free, lifetime без expiry
   - `check_memorial_limit`: free=1, plus=10, extra_slots, demo bypass
   - `check_chat_quota`: free=15, plus=200, lifetime locked memorial, demo bypass
   - `check_animation_quota`: free=0→402, plus=5, pro=15, demo bypass
   - `check_tts_access`: free→402, plus/pro/lifetime OK, demo bypass
   - `check_family_rag_access`: free+lifetime→402, plus/pro OK, demo bypass
   - `check_live_session_quota`: free/plus→402, pro=5, lifetime_pro pool, demo bypass
   - Инкременты: chat, animation, live_session, lifetime_pro pool decrement
   - HTTP-level: free plan limit via API (1st OK, 2nd → 402)
   - Переопределяем autouse через `_bypass_billing` в самом test_billing.py
3. Добавлены 8 новых тестов в `tests/test_access.py`:
   - `test_reject_access_request` — reject → нет доступа
   - `test_re_request_after_rejection` — upsert после reject → PENDING
   - `test_duplicate_request_upsert` — дубль → обновление, не дублирование
   - `test_request_when_already_have_access` → 400
   - `test_non_owner_cannot_list_access` → 403
   - `test_non_owner_cannot_see_access_requests` → 403
   - `test_cannot_revoke_only_owner` → 400
   - `test_approve_already_approved_request` → 400
4. Проверен стек: backend и frontend НЕ запущены, Redis OK, Qdrant embedded (через QDRANT_LOCAL_PATH)

**Итог:** 67/67 тестов прошли. Общий счёт теперь 125+67 = 192 теста.

**Изменённые файлы:**
- `backend/tests/test_billing.py` — новый файл (44 теста)
- `backend/tests/test_access.py` — +8 тестов

**Осталось сделать:**
- Запустить полный регресс (`pytest` всей suite)
- Закоммитить все незакоммиченные изменения (33 файла + demo mode)
- Запустить E2E тесты с живым стеком

---

## [2026-04-20] Баги инвайт/биллинг исправлены + демо-режим спроектирован
**Статус:** частично завершено (баги пофикшены, демо-режим НЕ реализован — токены закончились)

**Что сделали:**
1. Исправлен CRITICAL баг: `POST /ai/avatar/chat` не проверял `is_public` → анонимы могли читать воспоминания приватных мемориалов. Добавлена проверка + `require_memorial_access(VIEWER)` для авторизованных без доступа. Файл: `backend/app/api/ai.py`
2. `uses_count` инвайта инкрементировался при каждом открытии ContributePage (`validate_invite`), а не при реальном добавлении воспоминания. Перенесён инкремент в `create_memory`. Файлы: `api/invites.py`, `api/memorials.py`
3. `source` воспоминаний теперь `"invite"` при гостевом вкладе (было всегда `"user"`). Файл: `api/memorials.py`
4. `UPGRADE_URL` исправлен с `/app/pricing` (404) на `/#pricing`. Файл: `services/billing.py`

**Демо-режим — спроектировано, не реализовано:**
- 43 демо-мемориала уже в БД (`is_public=True`, `user_id=1`, `is_demo=True`)
- 4 семьи: Kelly, Anderson, Chang, Rossi — связаны деревом + hidden connections
- Нужно: `/demo` страница (DemoPage.jsx), баннер на `/m/:id`, кнопка "Try Demo" на логине
- Подробный план в HANDOFF.md

**Изменённые файлы:**
- `backend/app/api/ai.py`
- `backend/app/api/invites.py`
- `backend/app/api/memorials.py`
- `backend/app/services/billing.py`

**Осталось сделать:** Реализовать демо-режим (см. HANDOFF.md — 4 шага)

---

## [2026-04-20] /run-tests — pytest 125/125, E2E SKIPPED (backend offline)
**Статус:** завершено
**Что делали:** Запустили полный набор тестов. pytest — все 125 прошли. E2E упали потому что бэкенд не был запущен.
**Фиксы E2E:** RegisterPage.jsx + LoginPage.jsx — добавлены атрибуты `name=` на все input'ы (без них Playwright не мог найти поля). Установлен webkit (npx playwright install webkit) — мобильные тесты больше не падают с 0ms.
**Изменённые файлы:** `frontend/src/pages/RegisterPage.jsx`, `frontend/src/pages/LoginPage.jsx`
**Следующий шаг:** Запустить бэкенд + фронт и повторить E2E.

## [2026-04-18] Роли, уровни доступа, демо-аккаунты + подготовка к Stripe

**Статус:** завершено

**Что делали:**
- Добавили поле `User.is_demo` (Boolean, default=False) в models.py — демо-аккаунты bypass биллинга
- Обновили billing.py: все 5 check-функций теперь делают ранний return для is_demo=True
- Добавили `is_demo_account()` helper в billing.py
- Обновили UserResponse в schemas.py: добавили поля `is_demo` и `subscription_plan`
- Обновили seed_ensure_owner.py: демо-юзер id=1 создаётся с `is_demo=True`
- Создали `docs/ACCESS_LEVELS.md` — исчерпывающая документация ролей × тарифов + Stripe-план
- Обновили `docs/MONETIZATION.md`: ссылка на ACCESS_LEVELS.md

**Изменённые файлы:**
- `backend/app/models.py` — +`is_demo` поле на User
- `backend/app/schemas.py` — +`is_demo`, `subscription_plan` в UserResponse
- `backend/app/services/billing.py` — +`is_demo_account()`, bypass во всех check-функциях
- `backend/seed_ensure_owner.py` — `is_demo=True` для seed-юзера
- `docs/ACCESS_LEVELS.md` — новый файл (матрица ролей × планов, Stripe-план)
- `docs/MONETIZATION.md` — ссылка на ACCESS_LEVELS.md

**Важно для деплоя:**
- Нужна DB-миграция: `ALTER TABLE users ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT false;`
- В prod поставить `is_demo=True` для `en-demo@memorial.local` и `demo@memorial.app`

**Следующий шаг:** Stripe-интеграция — `POST /billing/checkout` + webhook + `PATCH /admin/users/{id}/plan`

## [2026-04-18] Supabase Storage — завершение миграции медиа

**Статус:** завершено

**Что делали:** Завершили миграцию 43 seed-медиа на Supabase Storage.

**Контекст:** `USE_S3=true`, Supabase S3 Access Keys уже были в `.env`, bucket `memorial-media` существовал, 43 портрета уже лежали в `portraits/` Supabase. Но `file_path` в БД указывал на `uploads/xxx.jpg`, а `thumbnail_path` — на `uploads/thumbnails/...`.

**Сделано:**
1. `backend/app/api/media.py` — фикс S3 fallback: теперь приоритет `media.file_url` → не нужно конструировать URL из `file_path` (было: `get_public_url(str(media.file_path))` → неправильный URL в проде)
2. БД: обновлены все 43 Media записи — `file_path` = `portraits/name.jpg` (S3-ключ, извлечён из `file_url`)
3. Supabase: загружены 43 thumbnails в `thumbnails/` префикс; `thumbnail_path` обновлён в БД

**Итог:**
- `file_path` → S3-ключ (`portraits/...`)
- `file_url` → публичный Supabase URL
- `thumbnail_path` → S3-ключ (`thumbnails/...`)
- Все новые загрузки уже шли в S3; аудио TTS тоже

**Изменённые файлы:**
- `backend/app/api/media.py` (строки ~113-118: fallback redirect)
- БД Supabase Postgres: таблица `media`, все 43 строк

## [2026-04-15] Монетизация — Вариант C, гейтинг фич

**Статус:** завершено

**Что делали:** Выбрали и реализовали монетизационную модель Вариант C.

**Изменения:**
- `frontend/landing/index.html` — обновлены цены: Plus $7/мес ($59/год), Lifetime $99; лимиты: Free 15 msg/мес, Plus 10 мемориалов / 200 msg / 5 анимаций
- `backend/app/models.py` — добавлен `SubscriptionPlan` enum; в `User`: `subscription_plan`, `plan_expires_at`, `lifetime_memorial_id`; новая таблица `UserUsage` (счётчики по периоду YYYY-MM)
- `backend/app/main.py` — миграция новых колонок users при старте
- `backend/app/services/billing.py` — СОЗДАН: `PLAN_LIMITS`, `check_memorial_limit`, `check_chat_quota`, `check_animation_quota`, `check_tts_access`, `check_family_rag_access`, `increment_*_usage`
- `backend/app/api/ai.py` — гейты в `avatar_chat` (chat quota + family RAG + TTS), `animate_photo` (animation quota, теперь требует auth), `upload_voice` (TTS gate, теперь требует auth)
- `backend/app/api/memorials.py` — `check_memorial_limit` перед созданием мемориала
- `docs/MONETIZATION.md` — перезаписан: лимиты, архитектура гейтинга, следующие шаги

**Следующие шаги:**
1. Stripe Checkout — `POST /billing/checkout`
2. Stripe Webhook — обновление плана в БД
3. `GET /billing/usage` — endpoint для UI (показывать остаток квоты)
4. Страница `/app/pricing` в React
5. Admin endpoint для ручного апгрейда при тестировании

## [2026-04-14] Family Tree Miro-like Editor — Drag + Draw Connections + DB Storage

**Статус:** завершено

**Что делали:** Реализовали интерактивный редактор семейного дерева: перетаскивание узлов, рисование связей мышью, сохранение в БД.

**Реализовано:**
1. **Backend**: новая колонка `tree_layout_json JSON` в `Memorial`, авто-миграция в `_add_missing_columns()`, поля в `MemorialUpdate` / `MemorialResponse`
2. **Frontend — Edit Mode**: кнопка `✎ Edit layout` в тулбаре (только для generations layout). В edit mode скрывается кнопка "Add relation"
3. **Drag nodes**: `onMouseDown` на карточках → `nodeDragRef` → `onMouseMove` на канвасе обновляет `nodeOverrides` → `stopPropagation` предотвращает pan. Scale-корректировка: delta / transform.scale
4. **Effective positions**: `effectivePositions = genLayout.positions + nodeOverrides`. Все коннекторы/маркеры пересчитываются из них
5. **Автосохранение**: debounce 800ms после drag end → PATCH /memorials/{id} с tree_layout_json
6. **Port handles**: 4 точки (top/right/bottom/left) появляются при hover в edit mode
7. **Draw connections**: drag от порта → temp SVG line следует за мышью → отпускание на другой карточке → модал выбора типа связи
8. **Edge drop detection**: `data-memorial-id` атрибут на карточках + `e.target.closest('[data-memorial-id]')` в onMouseUp
9. **Pending edge modal**: модал с выбором типа связи → POST /family/relationships → reload

**Изменённые файлы:**
- `backend/app/models.py` — `tree_layout_json = Column(JSON, nullable=True)` в Memorial
- `backend/app/main.py` — ALTER TABLE в `_add_missing_columns()`
- `backend/app/schemas.py` — `tree_layout_json` в MemorialUpdate + MemorialResponse
- `frontend/src/components/FamilyTree.jsx` — всё выше + новый state + handlers
- `frontend/src/components/FamilyTree.css` — стили edit toggle, port handles, pending edge modal
- `frontend/src/locales/en.js`, `ru.js` — новые ключи: edit_mode, edit_mode_exit, connect_title

**Не реализовано (отложено):**
- Клик по коннектору для удаления связи (сложно из-за thin SVG lines; удаление через список ниже дерева)
- Сброс позиций в auto-layout (кнопка "Reset layout")

**Верификация:** `npm run build` — OK, `python -c "from app.models import Memorial..."` — OK

## [2026-04-11] Family Tree GOT-style circles + stub fix + generation positioning

**Статус:** завершено

**Что делали:** Завершили переход на GOT-style визуализацию семейного дерева (круглые аватары вместо карточек) + исправили два бага.

**Bug 1 — ft-circle-info wrong position:** Текст (имя/годы) рендерился ПОВЕРХ аватара. `top: calc(100% - 44px)` при nodeH=118 даёт top=74px, тогда как аватар заканчивается на 80px. **Решение:** inline `style={{ top: avatarSize + 4 }}` в JSX для `GenTreeNodeCard` и `StubNodeCard`, убрали неправильное CSS правило.

**Bug 2 — Anderson stubs в неправильном поколении:** `computeLayoutDepthOldestTop` помещал Андерсон-стабы в G2 (по birth_year 1865) даже если их Kelly-сосед в G3. **Решение:** В `buildGenerationLayout`, после вычисления `layoutDepth`, в singleFamilyMode пробегаем все stub-узлы и переопределяем их глубину = среднее по gen их visible (non-stub) соседей.

**Изменённые файлы:**
- `frontend/src/components/FamilyTree.jsx` — top inline style в GenTreeNodeCard и StubNodeCard
- `frontend/src/components/FamilyTree.css` — убрано неправильное CSS `top: calc(100% - 44px)`
- `frontend/src/utils/familyTreeGenerationLayout.js` — stub generation snap в singleFamilyMode

**Осталось сделать:**
- Проверить визуально в браузере (Kelly-only режим → GOT circles → Anderson stubs на правильном поколении)
- Разблокировка Anderson → должен добавиться в дерево и показать cross-family связи

---

## [2026-03-29] Перевод ContributePage на i18n

**Статус:** завершено

**Что делали:** ContributePage.jsx использовал захардкоженные русские строки — не работал в EN-режиме. Подключили `useLanguage` и вынесли все строки в локализацию.

**Изменённые файлы:**
- `frontend/src/pages/ContributePage.jsx` — подключён `useLanguage`, все строки заменены на `t('contribute.*')`
- `frontend/src/locales/en.js` — добавлена секция `contribute` (35 ключей)
- `frontend/src/locales/ru.js` — добавлена секция `contribute` (35 ключей)

---

## [2026-03-28] Avatar chat split-layout
**Статус:** завершено
**Что делали:** Реализован новый дизайн AvatarChat — split layout (левая панель с фото аватара, правая с чатом). Desktop: row, 40%/60%. Mobile ≤768px: column, фото 220px сверху.
**Изменённые файлы:** `AvatarChat.jsx`, `AvatarChat.css`, `locales/en.js`, `locales/ru.js`
**Детали:** avatar-panel с полноразмерным фото (object-fit: cover), gradient footer (имя + статус-дот), thinking overlay при loading=true. Удалено дублирующее фото/avatar из chat-header.

---

## [2026-03-28] — /run-tests (полный тест связей)
**Статус:** pytest 116/116, E2E SKIPPED (backend offline)
**Упавшие тесты:** нет
**Новый файл:** `tests/test_family_relationships_full.py` — 46 тестов по всем типам связей

---

## [2026-03-28] Расширение типов семейных связей

**Статус:** завершено

**Что делали:** Добавили 7 новых типов + CUSTOM для произвольных связей.

**Новые типы:** step_parent/step_child, adoptive_parent/adoptive_child, half_sibling, partner, ex_spouse, custom (с полем custom_label).

**Изменённые файлы:**
- `backend/app/models.py` — расширен RelationshipType enum + поле custom_label
- `backend/app/schemas.py` — custom_label в FamilyRelationshipCreate/Response
- `backend/app/api/family.py` — REVERSE_MAP/DELETE_REVERSE_MAP, валидация custom_label
- `frontend/src/components/FamilyTree.jsx` — новые типы в select (с группами), поле custom_label, маппинг в дереве
- `frontend/src/locales/ru.js` + `en.js` — переводы

**Осталось:** Миграция production БД (Supabase) — добавить enum значения + колонку custom_label

---

## [2026-03-28] Фикс тестов: 70/70 passed

**Статус:** завершено ✅

**Что делали:** Запустили все pytest-тесты, нашли 70 падений/ошибок, исправили все.

**Проблемы и решения:**

1. **bcrypt 5.0.0 + passlib 1.7.4 несовместимы** → заменили passlib в `app/auth.py` на прямые вызовы `bcrypt.hashpw`/`bcrypt.checkpw`. Ошибка `ValueError: password cannot be longer than 72 bytes` даже для коротких паролей — известный баг.

2. **Старые тесты не использовали auth** → `test_memorials.py` полностью переписан (убран свой engine, используют conftest fixtures с `auth_client`); `test_memorials_extended.py` и `test_family_tree.py` — `client` заменён на `auth_client`.

3. **invites.py** — три проблемы: `create_invite` возвращал 200 вместо 201; `revoke_invite` возвращал `{"message": ...}` 200 вместо 204; `validate_invite` не принимал `expires_at` (только `expires_days`). Исправлены все три + добавлено поле `expires_at` и `permissions` в `InviteCreate` схему.

4. **Timezone naive vs aware** — SQLite возвращает naive datetimes, сравнение с `datetime.now(timezone.utc)` бросало `TypeError`. Исправлено в `invites.py::validate_invite` и `memorials.py::create_memory` — оба используют `datetime.utcnow()` для сравнения.

5. **family.py tree builder** — не обрабатывал `CHILD` тип отношений в `children_map`, только `PARENT`. Добавлена ветка для `CHILD`: `children_map[rel.memorial_id].append(rel.related_memorial_id)`.

6. **test_update_access_role** — не регистрировал второго пользователя (нужен `second_user_headers`); использовал `grant_resp.json()["id"]` вместо `user_id` (endpoint принимает user_id, не access entry id).

7. **Тесты анонимного доступа** — `auth_client` изменяет `client.headers` in-place, поэтому "anonymous" `client` всегда имел auth-заголовок. Решение: `monkeypatch("app.auth._get_dev_user", lambda db: None)` + явный `headers={"Authorization": ""}` в запросе.

**Изменённые файлы:**
- `backend/app/auth.py` — passlib → bcrypt
- `backend/app/api/invites.py` — status_code, expires_at, 204 delete, naive datetime
- `backend/app/api/memorials.py` — naive datetime в invite validation
- `backend/app/api/family.py` — CHILD в children_map
- `backend/app/schemas.py` — expires_at + permissions в InviteCreate
- `backend/tests/test_memorials.py` — переписан с auth_client
- `backend/tests/test_memorials_extended.py` — auth_client
- `backend/tests/test_family_tree.py` — auth_client
- `backend/tests/test_access.py` — second_user_headers + monkeypatch
- `backend/tests/test_invites.py` — monkeypatch + headers

**Результат:** 70/70 pytest passed, E2E: SKIPPED (backend offline)

**Осталось сделать:**
- MemorialDetail UI: роли по `current_user_role`
- i18n: MemorialPublic и другие страницы

---

## [2026-03-28] Синхронизация с Cursor + проверка MCP

**Статус:** завершено ✅

**Что делали:**
- Проверили установленные MCP серверы в проекте → не установлено ни одного (пустой `mcpServers` в обоих конфигах)
- Получили список 9 MCP из документа пользователя; приоритет: Supabase MCP + Browser MCP
- Обновили `HANDOFF.md` с полным состоянием проекта: Фазы 1-3 авторизации, незавершённые задачи, API endpoints

**Изменённые файлы:** `HANDOFF.md`

**Осталось сделать:**
- Фаза 2: UI шаринга в MemorialDetail (accessAPI в client.js + таб "Доступ")
- Фаза 3: Запрос доступа из MemorialPublic + панель approve/reject для owner
- Установить Supabase MCP и Browser MCP

---

## [2026-03-28] Фаза 1 авторизации: JWT + MemorialAccess + frontend auth

**Статус:** завершено ✅

**Что делали:**
Реализовали полную систему аутентификации и базовой авторизации (Фаза 1 из 3).

**Backend:**
- `backend/app/auth.py` — JWT utilities: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`; FastAPI dependencies: `get_current_user` (обязательный), `get_optional_user` (опциональный), `require_memorial_access(memorial_id, user, db, min_role, allow_public)` с иерархией ROLE_PRIORITY
- `backend/app/api/auth.py` — POST /auth/register, POST /auth/token (OAuth2), POST /auth/login (JSON), GET /auth/me
- `backend/app/models.py` — добавлена `MemorialAccess(id, memorial_id, user_id, role, granted_by, created_at)` + связи в User/Memorial
- `backend/app/schemas.py` — Token, TokenWithUser, LoginRequest (размещены ПОСЛЕ UserResponse — иначе Pydantic v2 падал с forward ref error); MemorialDetailResponse.current_user_role
- `backend/app/api/memorials.py` — убран `owner_id=1` везде; `create_memorial` auto-creates `MemorialAccess(OWNER)`; все write-endpoints защищены; read-endpoints используют `get_optional_user + allow_public=True`; `create_memory` поддерживает `?invite_token=` (проверяет MemorialInvite) для анонимных вкладчиков
- `backend/app/main.py` — убран `_ensure_default_user()`, добавлен `_migrate_existing_access()` (создаёт OWNER записи для существующих мемориалов при старте), добавлен auth router
- `backend/app/config.py` — ACCESS_TOKEN_EXPIRE_MINUTES=10080 (было 30)

**Frontend:**
- `frontend/src/context/AuthContext.jsx` — AuthProvider + useAuth hook; при монтировании читает localStorage → /auth/me для верификации
- `frontend/src/components/ProtectedRoute.jsx` — redirect /login если нет user
- `frontend/src/pages/LoginPage.jsx` + `RegisterPage.jsx` + `AuthPage.css` — формы входа/регистрации
- `frontend/src/App.jsx` — AuthProvider wrapper, /login и /register публичные, / /memorials/new /memorials/:id защищены через ProtectedRoute
- `frontend/src/api/client.js` — Bearer token interceptor (читает из localStorage), добавлены authAPI + createMemory принимает inviteToken
- `frontend/src/components/Layout.jsx` — показывает username + кнопку Выйти если авторизован, иначе Войти/Регистрация
- `frontend/src/pages/ContributePage.jsx` — передаёт `token` в `createMemory(..., token)`

**Проблемы и решения:**
- Pydantic v2 forward ref error: `TokenWithUser` ссылался на `"UserResponse"` строкой, но класс не был ещё определён. Решение: разместить Token schemas ПОСЛЕ UserResponse.
- `_migrate_existing_access`: нужно LEFT OUTER JOIN на условии `(memorial_id=X AND role=OWNER)` + `WHERE access.id IS NULL` — работает в SQLAlchemy через `.outerjoin(MemorialAccess, condition)`.

**Изменённые файлы:** см. HANDOFF.md

**Осталось сделать:**
- Фаза 2: `backend/app/api/access.py` + защита family.py/invites.py + UI шаринга в MemorialDetail
- Фаза 3: AccessRequest модель + "Запросить доступ" UI
- MemorialDetail: UI должен показывать owner-панель только при `current_user_role === 'owner'`

---

## [2026-03-25] E2E: семейный RAG — 5 пар, чеклист с ответами API

**Статус:** завершено (прогон на локальном backend + реальные ответы чата)

**Что делали:**
- Подобраны 5 пар (B=аватар, A=чужой мемориал с упоминанием B, ребро `family_relationships`: B→A).
- Выполнены `POST /api/v1/ai/avatar/chat` с `include_family_memories=true` (без аудио).
- Зафиксированы вопросы, ответы, оценки 1–5 соответствия опорному воспоминанию.

**Результат:** средняя оценка **4.6/5**; тесты 3 и 5 — частичное обобщение LLM (детали сида не дословно).

**Файл:** [docs/CROSS_MEMORIAL_RAG_CHECKS.md](docs/CROSS_MEMORIAL_RAG_CHECKS.md)

**Изменённые файлы:** `docs/CROSS_MEMORIAL_RAG_CHECKS.md` (новый), `SESSION_LOG.md`

---

## [2026-03-25] ENVIRONMENT.md: локально vs веб, MCP, Playwright

**Статус:** завершено

**Что делали:**
- Проверка MCP: в репозитории нет `mcp.json`; глобальный список MCP Cursor с диска не извлечён (конфиг в UI Cursor). Рекомендации: Git/GitHub, SQLite (read-only к `memorial.db`), опционально `@playwright/mcp` — зафиксированы в [ENVIRONMENT.md](ENVIRONMENT.md).
- Добавлен [ENVIRONMENT.md](ENVIRONMENT.md) — таблица локально/прод, `VITE_API_URL` vs прокси Vite, `backend/.env` (`DATABASE_URL`, `USE_S3`, `CORS_ORIGINS`, `PUBLIC_*`, `BOT_API_BASE_URL`), Qdrant, чеклист деплоя, раздел MCP.
- **Открытые вопросы / нерешённое:** пользователь сам проверяет в Cursor Settings → MCP, какие серверы реально включены; при деплое — актуализировать `VITE_API_URL` на Vercel и переменные Railway/бэкенда (не автоматизировалось).

**Изменённые файлы:**
- `ENVIRONMENT.md` — новый
- `SESSION_LOG.md` — эта запись

**Playwright:** ассистент может писать тесты на Playwright и использовать MCP `@playwright/mcp`, если пользователь добавит его в конфиг Cursor; в этом чате инструментов браузера по умолчанию может не быть.

---

## [2026-03-18] ElevenLabs ключ #3, краткие ответы аватара, аудио по умолчанию

**Статус:** завершено

**Что делали:**
- `backend/.env` — заменён `ELEVENLABS_API_KEY` на новый ключ #3
- `backend/app/services/ai_tasks.py` — промпт аватара на краткость (1–3 предложения), `max_tokens` 800→200
- `frontend/src/components/AvatarChat.jsx` — `includeAudio` по умолчанию `true`

**Изменённые файлы:** см. `HANDOFF.md` в корне (дата 2026-03-18).

---

## [2026-03-17] Питч-демо: QR-код inline display

**Статус:** завершено ✅

**Что делали:**
Реализовали inline отображение QR-кода для питч-демо (шаг 5 сценария: «Покажи QR-код на экране»).

**Изменения:**
1. `MemorialDetail.jsx` — кнопка «QR-код» теперь открывает модал с инлайн-изображением QR (220×220px), URL публичной страницы + кнопка «Копировать» + кнопка «Скачать PNG». Добавлено состояние `showQRModal`, `qrBlobUrl`, `qrLoading`.
2. `MemorialDetail.css` — новые стили `.qr-modal`, `.qr-modal-body`, `.qr-image`, `.qr-hint`, `.qr-url-row`, `.qr-url`.
3. `MemorialPublic.jsx` — добавлена секция «Поделиться QR-кодом» перед footer: кнопка → раскрывающийся панель с QR-изображением + URL + копировать + скачать. Переработан `handleDownloadQR` → `handleShowQR` + отдельный `handleDownloadQR`.
4. `MemorialPublic.css` — новые стили `.public-share-section`, `.btn-share-qr`, `.public-qr-panel`, `.public-qr-image`, `.public-qr-hint`, `.public-qr-url-row`, `.btn-copy-small`, `.btn-download-qr`.

**Проверка:** `npm run build` — ✅ 687ms, без ошибок.

**Изменённые файлы:**
- `frontend/src/pages/MemorialDetail.jsx`
- `frontend/src/pages/MemorialDetail.css`
- `frontend/src/pages/MemorialPublic.jsx`
- `frontend/src/pages/MemorialPublic.css`

---

## [2026-03-17] FamilyTree — полное имя + контраст живые/умершие

**Статус:** завершено ✅

**Что делали:**
- `NODE_W` 150→172, `NODE_H` 88→108 — место для полного ФИО
- `.ft-node-name` — убран `-webkit-line-clamp`, `word-break: break-word` — имя полностью
- `.ft-node--deceased` — тёмная карточка (bg rgba(38,30,24,0.88)), grayscale 60%, opacity 0.80; текст приглушён
- `.ft-node` — убран `overflow: hidden` чтобы имя не обрезалось по высоте
- `.ft-node-years` — font-weight 500 для читаемости дат

**Изменённые файлы:**
`frontend/src/components/FamilyTree.jsx` (NODE_W, NODE_H), `frontend/src/components/FamilyTree.css`

**Осталось:** Визуальная проверка

## [2026-03-17] FamilyTree — H-bracket коннекторы

**Статус:** завершено ✅

**Что делали:**
Заменили bezier-кривые «веер» на стандартный genealogy H-bracket паттерн в `ConnectionLines`.

**Изменения:**
- `V_GAP`: 100 → 120 (место для шины)
- `SPOUSE_GAP`: 16 → 20
- `BUS_DROP = 32` — новая константа (стем от knot до горизонтальной шины)
- Логика parent-child: вместо bezier от knot к каждому ребёнку отдельно — группировка детей по pairKey, затем: стем вниз от knot → горизонтальная шина → вертикальные дропы к каждому ребёнку
- Одиночный родитель (без пары): polyline с прямым углом через midY
- Линия супругов: `strokeWidth` 2.5, цвет `rgba(220,195,150,0.9)`, убран символ ∞ (заменён на `<title>Супруги</title>`)
- Knot-ромб: size 6 → 8px, `strokeWidth` 1 → 1.5

**Изменённые файлы:** `frontend/src/components/FamilyTree.jsx`

**Осталось сделать:** Визуальная проверка в браузере (npm run dev → localhost:5173 → мемориал → Семья)

## [2026-03-16] UI Редизайн «Warm Heritage 2.0» — полный цикл

**Статус:** завершено ✅

**Что делали:**
Реализовали полный редизайн CSS всех 13 файлов по плану «Warm Heritage 2.0». Только CSS, JSX не трогали.

**Ключевые изменения:**
1. `index.css` — новые токены (`--color-surface-hero`, `--color-accent-warm`, `--color-accent-light`, `--color-border-strong`, `--font-display`, `--font-body`, z-index система), `.btn-ghost`, улучшен `:focus-visible`, типографика h1-h4 с explicit line-height
2. `Layout.css` — underline анимация `scaleX 0→1`, отключён blur на мобиле, footer padding 2rem
3. `Home.css` — amber overlay, subtitle opacity 0.7, grid minmax 300px, card-name 1.4rem, card-dates 1rem, hover border-left accent, warm overlay на hover cover
4. `MemorialDetail.css` — теплее hero gradient, letter-spacing на name 0.02em, более заметные btn-icon с accent border, tabs 3px indicator + hover bg
5. `MemorialPublic.css` — memory card border-left 4px, photos grid 220px, contribute CTA с accent gradient border
6. `MemorialCreate.css` — form top border 3px accent-dark, select arrow accent-dark
7. `AvatarChat.css` — **КЛЮЧЕВОЕ**: переход на светлую тему (bg=surface, header=surface-warm, input=surface). Fullscreen сохраняет тёмную тему через `.avatar-chat--fullscreen` оверрайды.
8. `MediaGallery.css` — media item bg=surface-warm, audio placeholder warm, media actions bg=surface с border
9. `MemoryList.css` — border-left gradient (accent→accent-light), share panel в accent тонах вместо зелёного, btn-share в accent стиле
10. `FamilyTree.css` — **КЛЮЧЕВОЕ**: canvas bg тёмный коричнево-янтарный (`#1C1917→#5C3D22`), упрощены звёзды до 3 точек + warm dust, grayscale(40%) для deceased
11. `HiddenConnections.css` — весь UI переведён в светлую тему (surface-warm), hop colors → тёплая шкала (accent/accent-warm/amber/muted)
12. `LifeTimeline.css` — dot hover scale 1.5, card hover border-left accent, mobile year label fix
13. `ContributePage.css` — active tab box-shadow

**Проблем не было** — чистые CSS-изменения без затрагивания JSX/функционала.

**Изменённые файлы:**
`frontend/src/index.css`, `frontend/src/components/Layout.css`, `frontend/src/pages/Home.css`, `frontend/src/pages/MemorialDetail.css`, `frontend/src/pages/MemorialPublic.css`, `frontend/src/pages/MemorialCreate.css`, `frontend/src/components/AvatarChat.css`, `frontend/src/components/MediaGallery.css`, `frontend/src/components/MemoryList.css`, `frontend/src/components/FamilyTree.css`, `frontend/src/components/HiddenConnections.css`, `frontend/src/components/LifeTimeline.css`, `frontend/src/pages/ContributePage.css`

**Осталось сделать:** Визуальная проверка в браузере (npm run dev → localhost:5173)

## [2026-03-16] Склонение имён + фиксы видимости чата

**Статус:** завершено ✅

**Что делали:**
1. Создан `frontend/src/utils/declension.js` — утилита склонения русских имён (предложный + творительный падеж)
2. `MemoryList.jsx` — импорт `aboutName`, склонение в 3 местах (сообщение для шеринга, заголовок share, панель с приглашением)
3. `AvatarChat.jsx` — импорт `instrumentalName`, "Чат с Светланой Николаевной Морозовой" вместо именительного
4. `AvatarChat.css` — `.suggested-btn` стал видимым на светлом фоне: `bg=surface-warm`, `border=border-strong`, `color=accent-dark`
5. `MemorialDetail.css` — `.memorial-description` изменён с italic serif на `font-sans; font-style:normal; color: var(--text)` для читаемости

**Изменённые файлы:**
- `frontend/src/utils/declension.js` — новый файл
- `frontend/src/components/MemoryList.jsx` — import + 3 места склонения
- `frontend/src/components/AvatarChat.jsx` — import + instrumentalName в заголовке чата
- `frontend/src/components/AvatarChat.css` — `.suggested-btn` видимость
- `frontend/src/pages/MemorialDetail.css` — `.memorial-description` читаемость

---

## [2026-03-16] Тестирование голосовых аватаров + документация фичи

**Статус:** завершено ✅

**Что делали:**
Протестировали разделение голосов по полу аватара. Подтверждено рабочим:
- Мужской мемориал (`voice_gender=male`) → ElevenLabs голос `pNInz6obpgDQGcFmaJgB` (Adam)
- Женский мемориал (`voice_gender=female`) → ElevenLabs голос `EXAVITQu4vr4xnSDxMaL` (Bella)
- Фронтенд отправляет поле `include_audio` (не `generate_audio`!) в запросе

**Документация:** `VOICE_FEATURE.md` в корне проекта — полная шпаргалка по фиче:
точные файлы/строки, curl-тесты, таблица поломок и решений. Если голоса сломались после дизайн-изменений — смотреть туда.

**Ключевые файлы фичи:**
- `backend/app/api/ai.py` ~459–500 — логика выбора голоса
- `backend/app/services/ai_tasks.py` — функция `generate_speech_elevenlabs`
- `backend/app/schemas.py` — `AvatarChatRequest.include_audio`
- `frontend/src/components/AvatarChat.jsx` ~218, ~493 — отправка и рендер аудио
- `backend/.env` — `ELEVENLABS_VOICE_ID_MALE/FEMALE`

**Изменённые файлы:**
- `VOICE_FEATURE.md` — создан (документация)

---

## [2026-03-16] Полное наполнение воспоминаний всех 21 участника

**Статус:** завершено ✅

**Что делали:**
Изучили архитектуру family sync / relative memories (два механизма):
1. Query-time расширение поиска (`include_family_memories=True`) — ищет по Qdrant с фильтром всех родственников
2. Sync-агент (`POST /api/v1/ai/family/sync-memories/{id}`) — GPT-4 ищет упоминания родственников в воспоминаниях и создаёт отражённые Memory записи с `source="family_sync"`

Написан `backend/seed_memories_full.py` — добавляет полноценные воспоминания от детства до смерти/настоящего:
- Каждый из 21 участника получает 4-7 воспоминаний, охватывающих детство, юность, зрелость, старость
- Воспоминания содержат явные упоминания родственников по имени → работает family sync
- Скрипт идемпотентен (проверяет дубли по заголовку)

**Изменённые файлы:**
- `backend/seed_memories_full.py` — новый файл

**Следующий шаг:**
1. Запустить `python seed_memories_full.py` (нужен работающий Qdrant + OpenAI key)
2. Запустить family sync для ключевых мемориалов через POST /api/v1/ai/family/sync-memories/{id}

---

## [2026-03-16] Фото мемориалов + семейное дерево (pan/zoom + bidirectional)

**Статус:** завершено ✅

### 1. Фотографии мемориалов — исправление

**Проблема:** Изображения не отображались (broken image на главной и в деталях).

**Причина:** `USE_S3=true` → backend делает `RedirectResponse` на Supabase Storage URL. Скрипты сохраняли файлы **локально** в `backend/uploads/`, а не в Supabase. URL вида `supabase.co/storage/.../uploads/xxx.jpg` давал 400.

**Решение:**
1. `backend/fix_memorial_photos.py` — исправлен SSL баг (заменили `urllib.request` на `requests` библиотеку), скачал age/gender matched портреты с randomuser.me для мемориалов 20-31 (european nationalities: gb,ie,au,nz,fi,no,dk,nl)
2. `backend/fix_photos_tpdne.py` — новый скрипт для мемориалов 32-42, использует thispersondoesnotexist.com (AI-generated реалистичные лица) — randomuser.me заблокировал по rate-limit после 12 запросов (seed `d3adb33f` = error маркер)
3. `backend/upload_portraits_to_supabase.py` — загрузил все 23 локальных файла в Supabase Storage bucket `memorial-media` по ключу `uploads/{filename}.jpg`

**Итог:** media.id 11-33, все 23 мемориала (ID 20-42) имеют cover_photo, файлы в Supabase.

**Изменённые файлы:**
- `backend/fix_memorial_photos.py` — urllib→requests, SSL fix
- `backend/fix_photos_tpdne.py` — новый (thispersondoesnotexist.com)
- `backend/upload_portraits_to_supabase.py` — новый (upload to S3)

---

### 2. Семейное дерево — полный рефакторинг

**Проблема:** Старое дерево показывало только потомков от выбранного человека. Нет предков. Нет pan/zoom. Не работало слияние семей.

**Решение:**

**Backend** — новый endpoint `GET /family/memorials/{id}/full-tree?max_depth=6`:
- BFS по ВСЕМУ графу связей (не только потомки, но и предки)
- Каждому узлу присваивается **generation**: 0=root, -1=родители, -2=деды, +1=дети, +2=внуки
- Логика BFS: `parent` edge → generation-1, `child` → generation+1, `spouse/sibling` → то же поколение
- Возвращает плоский граф: `{ nodes: [...], edges: [...], root_id }`
- Схемы: `FullTreeNode`, `FullTreeEdge`, `FullFamilyTreeResponse` добавлены в `schemas.py`
- Слияние семей: если два дерева имеют общего предка — граф автоматически соединяется (BFS проходит через все связи в БД)
- Проверено: для мемориала 42 возвращает 21 узел, 41 ребро

**Frontend** — полный рерайт `FamilyTree.jsx` + `FamilyTree.css`:
- **Pan**: drag мышью + onTouchStart/Move одним пальцем
- **Zoom**: колёсико мыши (relative to cursor point) + pinch двумя пальцами (relative to pinch center)
- **Centration**: при загрузке автоматически центрируется на root node через `useEffect`
- **Layout**: `computeLayout()` группирует узлы по generation, в каждой строке — равномерное распределение
- **SVG overlay**: кривые Безье для parent-child линий, горизонтальные линии для супругов/сиблингов
- **Root node**: золотая рамка + цветная полоска сверху + двойной ring
- **Deceased nodes**: grayscale filter
- Тёмное небо со звёздами (signature canvas) сохранено

**Добавлен API метод** в `frontend/src/api/client.js`:
```js
getFullTree: (memorialId, maxDepth = 6) =>
  apiClient.get(`/family/memorials/${memorialId}/full-tree`, { params: { max_depth: maxDepth } }),
```

**`npm run build` ✅** — 721ms, без ошибок.

**Изменённые файлы:**
- `backend/app/schemas.py` — добавлены FullTreeNode, FullTreeEdge, FullFamilyTreeResponse
- `backend/app/api/family.py` — добавлен endpoint `full-tree`
- `frontend/src/api/client.js` — добавлен `getFullTree`
- `frontend/src/components/FamilyTree.jsx` — полный рерайт (pan/zoom canvas)
- `frontend/src/components/FamilyTree.css` — полный рерайт

**Известные ограничения / что можно улучшить:**
- Layout не оптимизирован: дети не центрируются под родителями (простое равномерное распределение по генерации). Можно улучшить алгоритмом Reingold-Tilford
- При большом дереве (50+ узлов) может быть перегружено — нужна виртуализация или level-of-detail
- Нет анимации перехода при смене центра (центрирование мгновенное)

---

## [2026-03-16] Редизайн UI — концепция "Тихий свет"

**Статус:** в процессе (6/9 файлов CSS завершено, ПРЕРВАН из-за лимита токенов)

**Что делали:**
Полный редизайн фронтенда. Концепция: "Тихий свет" — тёплая, не депрессивная палитра.
Дизайн-система: CSS-переменные в `index.css`, шрифты Cormorant Garamond + Inter (Google Fonts).

**Палитра:**
- `--bg: #FAF8F5`, `--surface-dark: #1C1917`
- `--accent: #C4A882` (золотисто-бежевый), `--accent-dark: #8B5E3C` (янтарь)
- `--border: #E8E0D4`, `--text: #3D3631`, `--text-muted: #8C7E6E`

**Изменённые файлы (ЗАВЕРШЕНО):**
- `frontend/src/index.css` — CSS vars, Google Fonts, base, buttons, form, animations
- `frontend/src/components/Layout.css` + `Layout.jsx` — sticky blur navbar, scroll state
- `frontend/src/pages/Home.css` + `Home.jsx` — hero dark + scroll cue + карточки с cover strip
- `frontend/src/pages/MemorialCreate.css` + `MemorialCreate.jsx` — centered card form
- `frontend/src/pages/MemorialDetail.css` + `MemorialDetail.jsx` — full-width hero overlay, новые tabs
- `frontend/src/components/AvatarChat.css` — тёмный чат, amber кнопки, cream пузыри
- `frontend/src/components/MemoryList.css` — gold left-border карточки
- `frontend/src/components/MediaGallery.css` — тёмный grid с hover zoom

**ОСТАЛОСЬ ДОДЕЛАТЬ (следующая сессия):**
1. `frontend/src/components/LifeTimeline.css` — золотая вертикальная линия, alternating layout
2. `frontend/src/components/FamilyTree.css` — warm cream nodes, accent lines
3. `frontend/src/pages/MemorialPublic.css` — read-only версия мемориала
4. `frontend/src/pages/ContributePage.css` — форма гостя
5. `frontend/src/components/HiddenConnections.css` — новый компонент
6. Проверить и починить если что-то сломалось в MemorialDetail.jsx (закрывающие теги + formatYear объявлен внутри return)

**Важный баг для проверки:**
В `MemorialDetail.jsx` функция `formatYear` объявлена внутри return JSX — нужно проверить что она перед return (возможно редактирование сместило код).



## [2026-03-15] Supabase интеграция + RAG фикс + деплой

**Статус:** завершено (остался 1 шаг — Vercel VITE_API_URL)

**Что делали:**

### 1. Дубликаты мемориалов — очистка SQLite
- Seed скрипт запускался 4 раза → 51 мемориал вместо 21
- Оставили IDs 1-21, удалили 22-51 (вместе с memories и family_relationships)
- cover_photo_id указывал на дублированные media (11-20) → исправили на оригинальные (1-10)

### 2. Supabase PostgreSQL
- Project ref `abbpyojdtlzkijcgmjzh` найден в `.claude/settings.local.json`
- Пароль сброшен → `AdcXpru0akzE2G6B`
- DATABASE_URL → Supabase Transaction Pooler (`aws-1-eu-central-1.pooler.supabase.com`)
- `db.py`: pool_pre_ping=True, pool_size=5, pool_recycle=300 для pgBouncer
- Работает: Railway отдаёт 10 мемориалов из Supabase

### 3. Supabase Storage (S3)
- Bucket `memorial-media` (PUBLIC, any MIME, 50MB Free tier)
- `config.py`: SUPABASE_URL, `s3_endpoint_url`, `supabase_public_url` properties
- `s3_service.py`: Supabase S3 endpoint + `get_public_url()`
- `media.py`: `RedirectResponse` на Supabase публичный URL при USE_S3=true (использует `media.thumbnail_path` из БД)
- `memorials.py`: thumbnails тоже идут в S3

### 4. Qdrant кластер
- eu-west-2 (`1a6a0d99`) → мёртв (404)
- Переключились на us-east-1 (`591a5520`) — работает
- `QDRANT_LOCAL_PATH` очищен

### 5. Embeddings — полное пересоздание
- 168 воспоминаний, только 14 имели embedding_id
- Коллекция пересоздана, все 168/168 embeddings созданы успешно

### 6. RAG chat — два фикса
**Фикс 1:** `qdrant-client 1.7.0` — `client.search()` удалён в 1.7+
- Обновили до `1.17.1`, заменили на `client.query_points()` в `ai_tasks.py`

**Фикс 2:** `min_score=0.5` — слишком высокий для text-embedding-3-small
- text-embedding-3-small даёт score 0.2-0.4 для релевантных текстов
- Снизили до `min_score=0.2`
- Проверено: для Анны Морозовой находит 3 воспоминания со score 0.38-0.47

### 7. Railway
- Все env vars обновлены через `railway variables set`
- `railway up --detach` — новый код задеплоен

**Изменённые файлы:**
`backend/.env`, `config.py`, `db.py`, `s3_service.py`, `media.py`, `memorials.py`, `ai_tasks.py`, `requirements.txt`

**Осталось сделать:**
- [ ] **КРИТИЧНО:** Vercel → Environment Variables → `VITE_API_URL=https://backend-production-e1e8.up.railway.app/api/v1` → Redeploy
- [ ] Фотографии в мемориалах Supabase: cover_photo_id=null у большинства (нет медиа — нужно залить фото)
- [ ] Проверить дубликаты в Supabase DB (там могут быть старые сиды)

## [2026-03-15] Фикс: аватарки мемориалов не отображались нигде

**Статус:** завершено

**Что делали:**
- Диагностировали, почему все изображения (главная, шапка мемориала, чат) показывали broken image
- Бэкенд: `USE_S3=true`, `DATABASE_URL` = Supabase PostgreSQL
- Реальный thumbnail_path в DB: `memorials/{id}/thumbnails/{uuid}_{name}_medium.jpg`
- Код в `media.py` вычислял: `{parent}/{stem}_{size}.jpg` = `memorials/{id}/{uuid}_{name}_small.jpg`
- Результат: URL без `thumbnails/` папки и с неверным суффиксом → 404 на Supabase

**Решение:**
- `media.py`: вместо вычисления thumb_key — использовать `media.thumbnail_path` из БД напрямую
- Если `thumbnail_path` есть → редирект на него; иначе → редирект на оригинальный файл

**Изменённые файлы:**
- `backend/app/api/media.py` — исправлена логика построения S3 ключа для миниатюр

**Проверено:** curl `media/1?thumbnail=small` → 302 на правильный Supabase URL → 200

---

## [2026-03-15] Оптимизация переключения вкладок + аватарки в семейном дереве

**Статус:** завершено

**Что делали:**
1. Убрали медленное пересоздание компонентов при смене вкладок — lazy mounting через `mountedTabs` Set
2. Исправили отсутствие фото в семейном дереве — бэкенд возвращал относительный URL (`/api/v1/media/...`), который в продакшне (Vercel+Railway) указывал на Vercel, а не на бэкенд
3. Оптимизировали N+1 запросы в `build_tree` — теперь 3 запроса вместо N*2+

**Проблемы и решения:**
- `cover_photo_url` в `FamilyTreeNode` хранил относительный URL вместо ID — заменили на `cover_photo_id` (int), фронтенд сам строит URL через `getMediaUrl()`
- `build_tree` делал по 1+ запросу на каждый узел — переписан на BFS: сначала собираем все ID, потом 1 батч-запрос для мемориалов, 1 для связей, дерево строим в памяти

**Изменённые файлы:**
- `backend/app/schemas.py` — `FamilyTreeNode`: заменено `cover_photo_url: str` → `cover_photo_id: int`
- `backend/app/api/family.py` — `get_family_tree`: bulk queries (BFS + 2 batch queries), убраны N+1 вызовы
- `frontend/src/components/FamilyTree.jsx` — импорт `getMediaUrl`, использование `node.cover_photo_id` вместо `node.cover_photo_url`
- `frontend/src/pages/MemorialDetail.jsx` — lazy mounting (`mountedTabs` Set), компоненты вкладок больше не перемонтируются

**Осталось сделать:** нет



## [2026-03-15] Фикс семейных деревьев + нативный фильтр Qdrant + cross-memorial RAG

**Статус:** завершено

**Что делали:**
1. Диагностировали и исправили критический баг в `build_tree` (`family.py`)
2. Добавили нативный Qdrant фильтр с `MatchAny` вместо Python-фильтрации
3. Создали payload index на поле `memorial_id` в Qdrant Cloud
4. Исправили `loadAvailableMemorials` в FamilyTree.jsx (заглушка → реальный API)
5. Заменили `input[type=number]` для ID на `select` с именами мемориалов

**Критический баг: build_tree (family.py)**
- Проблема: `build_tree` искал `CHILD` отношения от текущего узла, чтобы найти детей
- Семантика: `memorial_id=A, type=CHILD, related_memorial_id=B` = "A является ребёнком B"
  → дерево показывало РОДИТЕЛЕЙ как детей и не показывало реальных детей вообще
- Исправление: заменил `RelationshipType.CHILD` на `RelationshipType.PARENT`
  → `type=PARENT` значит "A является родителем B" — это правильный запрос для поиска детей
- Файл: `backend/app/api/family.py`

**Пример правильного дерева (после фикса):**
- Иван Морозов (3) ∞ Анна (4) → дети: Николай (5), Мария (6)
  - Николай (5) ∞ Людмила (10) → дети: Светлана (20), Александр (21)
- Фёдор Ковалёв (7) ∞ Прасковья (8) → дети: Пётр (9), Людмила (10)
  - Людмила ∞ Николай → дети: Светлана (20), Александр (21) [cross-family]

**Qdrant: призрачные embeddings и нативный фильтр:**
- В Qdrant Cloud 168 точек, но 30 из удалённых мемориалов (ID=11: 9шт, ID=12: 21шт)
- Старая реализация: Python-фильтрация после запроса без фильтра → призрачные embeddings занимали слоты
- Новая реализация: `MatchAny(any=memorial_ids)` через `query_filter` → нативная фильтрация
- Создан payload index: `client.create_payload_index('memorial-memories', 'memorial_id', INTEGER)`
- Файл: `backend/app/services/ai_tasks.py`

**Верификация cross-memorial RAG (E2E тест):**
- Вопрос "Расскажи о детях" для Николая (только memorial_5): 3 результата
- Вопрос "Расскажи о детях" для Николая + семья [5,3,4,10,20,21]: 30 результатов из всей семьи
- Вопрос "Расскажи о жене Людмиле" для [5,10]: 6 результатов из обоих мемориалов — работает!

**Состояние БД:**
- 10 мемориалов (ID: 3-10, 20, 21), 138 воспоминаний, 168 embeddings (30 призрачных, фильтруются)
- Все 10 мемориалов покрыты embeddings: 100%
- 36 семейных связей корректно отображают 2 семьи с пересечением через Людмилу (ID=10)

**Изменённые файлы:**
- `backend/app/api/family.py` — PARENT вместо CHILD в build_tree
- `backend/app/services/ai_tasks.py` — нативный фильтр Qdrant с MatchAny
- `frontend/src/components/FamilyTree.jsx` — loadAvailableMemorials + select вместо input

**Осталось сделать:**
- Запустить backend + frontend для визуальной проверки дерева
- Замена ELEVENLABS_API_KEY в .env на рабочий ключ (401 ошибка)

## [2026-03-11] Viral Share Button в MemoryList

**Статус:** завершено

**Что делали:** Встроили вирусную механику шеринга в компонент MemoryList и улучшили ContributePage.

**Изменённые файлы:**
- `frontend/src/components/MemoryList.jsx` — добавлен prop `memorialName`, кнопка "Пригласить друга", SharePanel с URL-копированием и Web Share API
- `frontend/src/components/MemoryList.css` — стили для `.memory-header-actions`, `.btn-share`, `.share-panel`, `.share-url-row`, `.btn-copy`, `.share-message-section`
- `frontend/src/pages/MemorialDetail.jsx` — передаётся `memorialName={memorial.name}` в MemoryList
- `frontend/src/pages/ContributePage.jsx` — тёплый текст в шапке, подсказка перед кнопкой записи, кнопка "Поделиться дальше" после сохранения с вирусной петлёй
- `frontend/src/pages/ContributePage.css` — стили для `.save-success-hint`, `.save-success-actions`, `.btn-viral-share`, `.record-hint`

## [2026-03-10] Подготовка демо для инвесторов

**Статус:** завершено

**DB засеяна:** 10 мемориалов + 141+ воспоминание + портреты + cover_photo_id для всех

## [2026-03-08] Улучшение читаемости семейного дерева
**Статус:** завершено
**Изменения:**
- FamilyTree.jsx: `renderTreeNode(node, level, relationLabel)` — новый параметр; словарь `RELATION_LABELS`; бейджи над именем в каждой карточке
- FamilyTree.css: `.node-relation-badge` (child=синий, spouse=розовый, root=серо-лиловый)

## [2026-03-08] Family Memory Synchronization — Layer 1 + Layer 2

**Статус:** завершено

**Layer 1 (real-time Cross-Memorial RAG):**
- `backend/app/schemas.py` — поле `include_family_memories: bool = False` в `AvatarChatRequest`
- `backend/app/services/ai_tasks.py` — `search_similar_memories()` принимает `memorial_ids: List[int]`
- `backend/app/api/ai.py` — family lookup + контекстные метки + family system prompt

**Layer 2 (Memory Sync Agent):**
- `backend/app/services/ai_tasks.py` — `sync_family_memories()`
- `backend/app/api/ai.py` — endpoint `POST /ai/family/sync-memories/{id}?dry_run=true`
- `frontend/src/components/AvatarChat.jsx` — кнопка "🔄 Синхр. с семьёй"

## [2026-03-07] Фикс чата с аватаром — Qdrant Cloud недоступен

**Статус:** завершено

**Решение:** Переключились на локальный файловый режим Qdrant.
Позже переключились обратно на Cloud (us-east-1-1): QDRANT_URL задан в .env

## 2026-04-19 — /run-tests + Stripe интеграция
**Статус:** завершено
**Что делали:** 
- Запустили pytest: 125/125 ✅
- E2E: SKIPPED — Playwright browsers не установлены (`npx playwright install` не запускался)
- Нашли баг: в memorial.spec.js:170 orphan-код вне test() — пофикшен, добавлен заголовок "13.7 Мобайл: карточки мемориалов не выходят за ширину 375px"
- Добавлены Pro + Lifetime Pro на лендинг (landing/index.html)
- Stripe интеграция: billing.py роутер, 4 endpoint'а, config.py с STRIPE_* переменными
**Изменённые файлы:** e2e/tests/memorial.spec.js, docs/TEST_PLAN.md, backend/app/api/billing.py, backend/app/config.py, backend/requirements.txt
**Осталось сделать:** npx playwright install chromium; заполнить STRIPE_* в .env и подключить webhook в Stripe Dashboard
