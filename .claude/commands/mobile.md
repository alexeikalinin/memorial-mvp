Проверь и улучши мобильную адаптацию интерфейса memorial-mvp.

Аргумент (опционально): $ARGUMENTS — конкретный компонент или страница для проверки.

## Шаг 1: Найди проблемные места в CSS

Прочитай параллельно все CSS файлы:
- `frontend/src/pages/Home.css`
- `frontend/src/pages/MemorialDetail.css`
- `frontend/src/pages/MemorialPublic.css`
- `frontend/src/components/AvatarChat.css`
- `frontend/src/components/MediaGallery.css`
- `frontend/src/components/MemoryList.css`
- `frontend/src/components/FamilyTree.css`
- `frontend/src/components/LifeTimeline.css`

Ищи антипаттерны мобильной вёрстки:
- Фиксированная ширина в px без `max-width` (например `width: 800px`)
- `position: fixed` без учёта мобильного viewport
- Шрифты < 14px (нечитаемо на мобиле)
- `overflow: hidden` на body/html (блокирует скролл)
- Flex/grid без `flex-wrap` или без мобильных брейкпоинтов
- Кнопки/ссылки с `height` < 44px (минимальная зона касания)
- Горизонтальный скролл (элементы шире viewport)
- `@media` брейкпоинты: есть ли вообще, правильные ли (mobile-first или desktop-first)

## Шаг 2: Проверь JSX компоненты

Прочитай соответствующие JSX файлы для найденных проблем:
- `frontend/src/pages/MemorialDetail.jsx` — табы, сложный layout
- `frontend/src/components/AvatarChat.jsx` — чат интерфейс
- `frontend/src/components/MediaGallery.jsx` — галерея фото/видео

Ищи:
- Инлайн стили с фиксированными размерами
- Отсутствие `viewport meta` в `index.html`
- Некликабельные элементы на мобиле

## Шаг 3: Проверь index.html

Прочитай `frontend/index.html`:
- Есть ли `<meta name="viewport" content="width=device-width, initial-scale=1.0">`

## Шаг 4: Выдай отчёт

Выведи таблицу найденных проблем:

| Файл | Строка | Проблема | Серьёзность | Исправление |
|------|--------|----------|-------------|-------------|

Серьёзность: КРИТИЧНО / ВАЖНО / УЛУЧШЕНИЕ

Затем для каждой КРИТИЧНО проблемы — сразу примени исправление через Edit.

## Шаг 5: Добавь базовые мобильные стили (если отсутствуют)

Если в файле нет `@media (max-width: ...)` вообще — добавь минимальный набор:

```css
@media (max-width: 768px) {
  /* основной контейнер — убрать горизонтальные отступы */
  /* шапка — упростить */
  /* кнопки — увеличить зону касания до 44px */
  /* текст — минимум 14px */
}
```

## Шаг 6: Итог

Выведи:
- Сколько проблем найдено (критичных / важных / улучшений)
- Какие исправления применены сейчас
- Какие требуют ручной проверки в браузере
- Команда для запуска: `cd frontend && npm run dev` → открой в DevTools → мобильный режим (375px)
