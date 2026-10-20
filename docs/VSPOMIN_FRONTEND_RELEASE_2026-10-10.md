# Выпуск домена, тарифов и мобильного лендинга — 10.10.2026

Основа: опубликованный commit12324d3528ba4fefbcdbaf9444b0226b1dc199ee. Изолированный исходник /private/tmp/vspomin-domain-pricing-release; прочие локальные изменения не опубликованы.

## Изменения

- Railway FRONTEND_URL=https://vspomin.ai/app; PUBLIC_FRONTEND_URL=https://vspomin.ai; добавлен CORS https://vspomin.ai с сохранением старых origins. Deployment9989516e-d3d6-409e-8698-73144dad363e SUCCESS; OPTIONS новый origin HTTP200 и правильный allow-origin.
- Vercel production VITE_API_URL=https://api.vspomin.ai/api/v1, landing API использует тот же адрес.
- Проектное правило vspomin-domain-migration IDaae601a5-ba4b-47d7-b7e1-f6f70969c7ab: source ^/(.*)$ regex, destination https://vspomin.ai/$1, status307, host только memorial-mvp.vercel.app. Проверено /app/pricing?next=%2Fm%2F1: путь/query сохранены. Первая конфигурация path-to-regexp с :path* добавляла лишнюю звёздочку; исправлена и проверена.
- PricingPage соответствует лендингу: Plus40/год, Family80/год, Family Pro140/год, индивидуальный Lifetime. Квоты показаны как будущий каталог; старый checkout убран с этой страницы. Действующие подписки/база/webhooks/расчёт backend квот не менялись. Заявки через существующий раздел /#pricing, как на лендинге.
- На мобильном лендинге hero-visual теперь видим, пример разговора под фото; ссылка /app/demo убрана. Проверены загрузка изображений и отсутствие горизонтального переполнения в браузере. Применено и к двум рабочим копиям landing; неопубликованный дизайн этих копий не выпускался.

## Публикации и восстановление

До доменного переключения: memorial-4is9ag3zb-1alexeikalinin1-3683s-projects.vercel.app. После только env: memorial-q838o5enj-1alexeikalinin1-3683s-projects.vercel.app. После тарифов: memorial-kyz7xe5g8-1alexeikalinin1-3683s-projects.vercel.app. После мобильного лендинга: memorial-ojuyduv1c-1alexeikalinin1-3683s-projects.vercel.app (dpl_Dn1cJp5qafTFbsP8E6iD1FUP4oj2).

Для отката только тарифов/мобильного лендинга: vercel rollback memorial-q838o5enj-1alexeikalinin1-3683s-projects.vercel.app --scope 1alexeikalinin1-3683s-projects. Env и Google остаются новыми. Для отката только мобильного лендинга: rollback memorial-kyz7xe5g8-1alexeikalinin1-3683s-projects.vercel.app.

Для полного отката домена: сначала vercel routes disable vspomin-domain-migration, затем vercel routes publish --yes (scope выше); это снимает переадресацию со старого домена. Затем восстановить env/Vercel deployment по GOOGLE_AUTH_MIGRATION_RUNBOOK_2026-10-10.md и VSPOMIN_DOMAIN_AUDIT_2026-10-10.md. Старые callback/API endpoint сохранены.

При следующем Git deploy включить PricingPage.jsx/PricingPage.css и мобильный patch landing, иначе Git вернёт прошлые версии. База не менялась.

## Итоговая проверка

Vercel dpl_Dn1cJp5qafTFbsP8E6iD1FUP4oj2 READY, alias vspomin.ai. Главная и /app/pricing HTTP200; HTML/SPA bundle не содержат backend-production-e1e8, JS использует https://api.vspomin.ai/api/v1 и новый каталог. Chrome на ширине320: scrollWidth314, hero display block, все изображения загружены, demo links0. Снимок портрета artifacts/domain-migration/mobile-landing-vspomin.jpg. Полный Google login после нового frontend return требует повторного входа владельца на новом origin; предыдущее Google API переключение уже проверено им.

Точный cumulative patch относительно12324d3: VSPOMIN_FRONTEND_RELEASE_2026-10-10.patch. Это позволяет повторить выпуск без остальных рабочих изменений.
