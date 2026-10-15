# Утверждённый выпуск frontend — 10.10.2026

Vercel deployment dpl_62azKzWBN1RoXQeZxMZv6EM4wN7K READY, https://memorial-8793kmthj-1alexeikalinin1-3683s-projects.vercel.app, alias https://vspomin.ai.

Изолированный исходник /private/tmp/vspomin-approved-release: git12324d3 +14 frontend/landing файлов. Публикация CLI, без Git push и без backend изменений. Сохранены текущие PricingPage.jsx/css, domain env и маршрутизация. Опубликованы тёмный минималистичный лендинг, mobileheader, вертикальное дерево, QRlayout/RUdemo, signs/appearancecopy, footerlogo, mobilemenu/candle/media и usernamehint.

Точный cumulative patch относительно12324d3: VSPOMIN_APPROVED_FRONTEND_RELEASE_2026-10-10.patch. Его необходимо включить в следующий Git release, чтобы не потерять CLI изменения.

Проверки: Vercel build passed. Live mobile390 landing HTTP200, allimages loaded, nooverflow/pageerrors; register hint найден, loginforgotlink доступен. До выпуска backend34authtests и UIforgot/reset наdisposableDB passed. Реальная доставка email не проверена. PrivateownerUI mobile проверен наlocalfixture.

Откат только этого выпуска: vercel rollback memorial-ojuyduv1c-1alexeikalinin1-3683s-projects.vercel.app --scope 1alexeikalinin1-3683s-projects. Domain/env остаются прежними. Предыдущий выпуск dpl_Dn1cJp5qafTFbsP8E6iD1FUP4oj2.
