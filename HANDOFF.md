# Handoff — Memorial MVP
> Обновлено: 2026-10-08
> Ветка: main

## Текущий фокус
Логотип 2 и фонарь 3 применены на главной. Для выбора новой композиции подготовлены три реалистичных семейных альбома с вымышленными AI-фотографиями: /app/album-composition-preview.html (ссылка есть в прежнем hero-composition-preview.html). Цитата/голос центрированы, иллюстративная подпись убрана. Пользователь выбрал первый льняной альбом: применён в Home, вся композиция сдвинута на 30px левее (mobile без сдвига). LemonSlice отложен до оплаты.

## Последнее действие
Добавлено клонирование голоса из MP4/MOV/M4V/WEBM: локальное извлечение MP3 через FFmpeg, обновлена проверка и подсказки формы. 6 серверных тестов и frontend build успешны. Публикация GitHub→Vercel/Railway. Подробности: [SESSION_LOG.md](SESSION_LOG.md).

## Следующий шаг
Проверить QR на реальном телефоне и Stripe test-mode webhook/Checkout; live OpenAI grounding уже проверен на вымышленных данных. Новая таблица guest_chat_usage создаётся при старте.

После оплаты LemonSlice проверить подключение photo + streaming Fish voice + existing RAG. Starter на дату проверки: $8/month, 41 included minutes, 3 baseline concurrent sessions, unlimited avatars; стоимость и правила перепроверить перед покупкой. Осталось отдельно live проверить multi-upload/листание нескольких фото. Домены отложены. Окружения: [ENVIRONMENT.md](ENVIRONMENT.md).
