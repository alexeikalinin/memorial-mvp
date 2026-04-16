# Полный план тестирования — Memorial MVP
> Создан: 2026-04-12 | Охват: backend (pytest) + E2E (Playwright)

---

## Условные обозначения

| Метка | Значение |
|-------|----------|
| ✅ | Уже покрыт существующими тестами |
| ⚠️ | Частично покрыт |
| ❌ | Не покрыт — нужно добавить |
| 🔴 | Критично (блокирует базовую работу) |
| 🟡 | Важно |
| 🟢 | Желательно |

---

## Блок 1. Аутентификация

### 1.1 Регистрация
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 1.1.1 | Регистрация с валидными данными (email, username, password ≥8) | 200, токен + user object | ✅ | 🔴 |
| 1.1.2 | Дублирующийся email | 400, "email already registered" | ✅ | 🔴 |
| 1.1.3 | Дублирующийся username | 400, "username already taken" | ✅ | 🔴 |
| 1.1.4 | Пароль < 8 символов | 422, validation error | ✅ | 🟡 |
| 1.1.5 | Пустой email / некорректный формат | 422 | ❌ | 🟡 |

### 1.2 Вход (login)
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 1.2.1 | Успешный вход (email + пароль) | 200, access_token | ✅ | 🔴 |
| 1.2.2 | Неверный пароль | 401 | ✅ | 🔴 |
| 1.2.3 | Несуществующий email | 401 | ✅ | 🔴 |
| 1.2.4 | GET /auth/me с валидным токеном | 200, user object | ✅ | 🔴 |
| 1.2.5 | GET /auth/me без токена | 401 | ✅ | 🔴 |
| 1.2.6 | GET /auth/me с протухшим токеном | 401 | ❌ | 🟡 |
| 1.2.7 | GET /auth/me с невалидным JWT (corrupted) | 401 | ❌ | 🟡 |

### 1.3 OAuth / Google
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 1.3.1 | GET /auth/google → redirect на Google | 302, Location = accounts.google.com | ❌ | 🟢 |
| 1.3.2 | GET /auth/google/callback с валидным кодом | токен в query params, редирект на /auth/callback | ❌ | 🟢 |

---

## Блок 2. Создание и управление мемориалом

### 2.1 Создание мемориала
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 2.1.1 | POST /memorials/ — минимальные поля (name only) | 200, memorial с owner_id=current_user | ✅ | 🔴 |
| 2.1.2 | POST /memorials/ — все поля (name, desc, dates, is_public, language) | 200, все поля сохранены | ✅ | 🔴 |
| 2.1.3 | POST /memorials/ без авторизации | 401 | ❌ | 🔴 |
| 2.1.4 | Создатель автоматически получает роль OWNER | GET /memorials/:id/access → role=owner | ❌ | 🔴 |
| 2.1.5 | Создание с language=en | memorial.language == "en" | ❌ | 🟡 |
| 2.1.6 | Создание с is_public=true | memorial.is_public == true | ✅ | 🟡 |

### 2.2 Чтение мемориала
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 2.2.1 | GET /memorials/ — список своих мемориалов | 200, array с created memorial | ✅ | 🔴 |
| 2.2.2 | GET /memorials/:id — owner видит детальный view | 200, current_user_role=owner | ✅ | 🔴 |
| 2.2.3 | GET /memorials/:id — публичный мемориал без авторизации | 200 | ❌ | 🔴 |
| 2.2.4 | GET /memorials/:id — приватный мемориал без авторизации | 401 или 403 | ❌ | 🔴 |
| 2.2.5 | GET /memorials/:id — несуществующий ID | 404 | ✅ | 🟡 |
| 2.2.6 | GET /memorials/:id/qr — QR-код в PNG | 200, Content-Type: image/png | ❌ | 🟢 |

### 2.3 Обновление мемориала
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 2.3.1 | PATCH /memorials/:id — owner обновляет name | 200, name обновлён | ✅ | 🔴 |
| 2.3.2 | PATCH /memorials/:id — editor обновляет name | 200 (editor имеет права) | ❌ | 🔴 |
| 2.3.3 | PATCH /memorials/:id — viewer пытается обновить | 403 | ❌ | 🔴 |
| 2.3.4 | PATCH /memorials/:id — без авторизации | 401 | ❌ | 🔴 |
| 2.3.5 | PATCH — переключение is_public true→false | мемориал становится приватным | ❌ | 🟡 |

### 2.4 Удаление мемориала
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 2.4.1 | DELETE /memorials/:id — owner удаляет | 200, memorial исчез из списка | ✅ | 🔴 |
| 2.4.2 | DELETE /memorials/:id — editor пытается удалить | 403 | ❌ | 🔴 |
| 2.4.3 | DELETE /memorials/:id — viewer пытается удалить | 403 | ❌ | 🔴 |
| 2.4.4 | DELETE — удаление чистит media/memories в БД | orphan records отсутствуют | ❌ | 🟡 |

---

## Блок 3. Медиафайлы

### 3.1 Загрузка медиа
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 3.1.1 | POST .../media/upload — загрузка PNG (owner) | 200, media_id, file_url | ❌ | 🔴 |
| 3.1.2 | POST .../media/upload — загрузка JPEG (owner) | 200 | ❌ | 🔴 |
| 3.1.3 | POST .../media/upload — загрузка видео MP4 (owner) | 200 | ❌ | 🟡 |
| 3.1.4 | POST .../media/upload — editor загружает фото | 200 (editor имеет права) | ❌ | 🔴 |
| 3.1.5 | POST .../media/upload — viewer загружает фото | 403 | ❌ | 🔴 |
| 3.1.6 | POST .../media/upload — без авторизации | 401 | ❌ | 🔴 |
| 3.1.7 | Загрузка файла > MAX_UPLOAD_SIZE | 413 или 400 | ❌ | 🟡 |
| 3.1.8 | Загрузка .exe / недопустимый формат | 400 | ❌ | 🟡 |
| 3.1.9 | Загрузка изображения создаёт thumbnails | thumbnail_path не null | ❌ | 🟡 |

### 3.2 Получение медиа
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 3.2.1 | GET /media/:id — скачать файл | 200, бинарные данные | ❌ | 🔴 |
| 3.2.2 | GET /media/:id?thumbnail=small | 200, thumbnail | ❌ | 🟡 |
| 3.2.3 | GET /media/:id?thumbnail=medium | 200, thumbnail | ❌ | 🟡 |
| 3.2.4 | GET /media/:id/info — метаданные | 200, size/type/dimensions | ❌ | 🟢 |
| 3.2.5 | GET /memorials/:id/media — список медиа | 200, array | ❌ | 🔴 |

### 3.3 Удаление и обложка
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 3.3.1 | DELETE .../media/:mediaId — owner удаляет фото | 200, файл удалён | ❌ | 🟡 |
| 3.3.2 | PATCH /memorials/:id — установить cover_photo_id | memorial.cover_photo_id обновлён | ✅ | 🟡 |
| 3.3.3 | PATCH /memorials/:id — снять cover (cover_photo_id=null) | cover_photo_id=null | ✅ | 🟡 |

---

## Блок 4. Воспоминания (Memories)

### 4.1 Создание воспоминаний
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 4.1.1 | POST .../memories — owner добавляет memory (title+content) | 200, memory_id | ✅ | 🔴 |
| 4.1.2 | POST .../memories — editor добавляет memory | 200 | ✅ | 🔴 |
| 4.1.3 | POST .../memories — viewer пытается добавить | 403 | ❌ | 🔴 |
| 4.1.4 | POST .../memories — без авторизации, без invite_token | 401 | ❌ | 🔴 |
| 4.1.5 | POST .../memories с invite_token (гость без аккаунта) | 200, memory создана | ✅ | 🔴 |
| 4.1.6 | POST .../memories — с event_date | memory.event_date сохранён | ✅ | 🟡 |
| 4.1.7 | Создание memory запускает embedding задачу | embedding_id появляется (async) | ⚠️ | 🟡 |

### 4.2 Чтение, обновление, удаление
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 4.2.1 | GET .../memories — список всех memories | 200, array | ✅ | 🔴 |
| 4.2.2 | GET .../memories?q=keyword — поиск | 200, только совпадения | ✅ | 🟡 |
| 4.2.3 | PATCH .../memories/:id — owner обновляет контент | 200, content обновлён | ✅ | 🔴 |
| 4.2.4 | PATCH .../memories/:id — viewer пытается обновить | 403 | ❌ | 🔴 |
| 4.2.5 | DELETE .../memories/:id — owner удаляет | 200, memory исчезла | ✅ | 🔴 |
| 4.2.6 | DELETE .../memories/:id — viewer пытается удалить | 403 | ❌ | 🔴 |

### 4.3 Timeline
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 4.3.1 | GET .../timeline — memories с датами идут в хронологическом порядке | порядок по event_date | ✅ | 🟡 |
| 4.3.2 | GET .../timeline — memories без дат идут в конце | undated в конце | ✅ | 🟡 |
| 4.3.3 | GET .../timeline — пустой мемориал | 200, пустой массив | ✅ | 🟢 |

---

## Блок 5. Чат с аватаром (RAG)

### 5.1 Базовый чат
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 5.1.1 | POST /ai/avatar/chat — чат с мемориалом без memories | 200, ответ без контекста | ✅ | 🔴 |
| 5.1.2 | POST /ai/avatar/chat — чат с мемориалом с 1+ memories | 200, ответ использует memories (sources не пустой) | ✅ | 🔴 |
| 5.1.3 | POST /ai/avatar/chat — несуществующий memorial_id | 404 | ❌ | 🔴 |
| 5.1.4 | POST /ai/avatar/chat — пустой question | 422 или 400 | ❌ | 🟡 |
| 5.1.5 | POST /ai/avatar/chat с include_audio=false | audio_url = null | ✅ | 🟡 |
| 5.1.6 | POST /ai/avatar/chat с include_audio=true (ElevenLabs настроен) | audio_url не null | ❌ | 🟡 |
| 5.1.7 | POST /ai/avatar/chat — use_persona=true | ответ с персоной (мок OpenAI) | ⚠️ | 🟡 |
| 5.1.8 | POST /ai/avatar/chat с language=en | ответ на английском | ❌ | 🟡 |

### 5.2 Family RAG
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 5.2.1 | Чат с include_family_memories=true — поиск идёт по related мемориалам | sources из родственных мемориалов | ❌ | 🟡 |
| 5.2.2 | Чат с include_family_memories=false — только свои memories | sources только из текущего мемориала | ❌ | 🟡 |

### 5.3 Embeddings
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 5.3.1 | GET /embeddings/memorials/:id/status — покрытие embeddings | coverage_percent, total, with_embeddings | ❌ | 🟡 |
| 5.3.2 | POST /embeddings/memories/:id/recreate — пересоздание embedding | 200, задача запущена | ❌ | 🟡 |
| 5.3.3 | POST /embeddings/memorials/:id/recreate-all | 200, все задачи запущены | ❌ | 🟡 |

---

## Блок 6. Система приглашений (Invite / Sharing)

### 6.1 Создание инвайта
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 6.1.1 | POST /invites/memorials/:id/create — owner создаёт инвайт | 200, token (64 chars) | ✅ | 🔴 |
| 6.1.2 | POST /invites/memorials/:id/create — editor создаёт инвайт | 200 (editor имеет права) | ✅ | 🔴 |
| 6.1.3 | POST /invites/memorials/:id/create — viewer пытается создать | 403 | ❌ | 🔴 |
| 6.1.4 | Инвайт с expires_days=7 | expires_at = now + 7 days | ✅ | 🟡 |
| 6.1.5 | Инвайт без expires_days | expires_at = null (бессрочный) | ✅ | 🟡 |
| 6.1.6 | Инвайт с кастомными permissions | permissions сохранены в БД | ❌ | 🟡 |
| 6.1.7 | Инвайт с label="Друзья" | label сохранён | ✅ | 🟢 |

### 6.2 Валидация инвайта
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 6.2.1 | GET /invites/validate/:token — валидный токен | 200, memorial_name + permissions | ✅ | 🔴 |
| 6.2.2 | GET /invites/validate/:token — несуществующий токен | 404 | ✅ | 🔴 |
| 6.2.3 | GET /invites/validate/:token — просроченный токен | 400 "expired" | ✅ | 🔴 |
| 6.2.4 | Валидация инкрементирует uses_count | uses_count +1 | ✅ | 🟡 |

### 6.3 Использование инвайта (гостевой вклад)
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 6.3.1 | POST .../memories?invite_token=TOKEN — гость добавляет memory | 200, memory создана | ✅ | 🔴 |
| 6.3.2 | POST .../memories — инвайт для другого мемориала | 403 | ✅ | 🔴 |
| 6.3.3 | POST .../memories — просроченный токен | 400 | ✅ | 🔴 |
| 6.3.4 | POST .../memories — инвайт с add_memories=false | 403 | ❌ | 🟡 |
| 6.3.5 | /contribute/:token — страница открывается без авторизации (E2E) | видна форма добавления | ⚠️ | 🔴 |

### 6.4 Управление инвайтами
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 6.4.1 | GET /invites/memorials/:id/list — список инвайтов | 200, array | ✅ | 🟡 |
| 6.4.2 | DELETE /invites/:token — отзыв инвайта (owner) | 200, токен удалён | ✅ | 🟡 |
| 6.4.3 | После отзыва — валидация токена даёт 404 | 404 | ✅ | 🟡 |

---

## Блок 7. Контроль доступа (RBAC)

### 7.1 Выдача доступа
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 7.1.1 | POST /memorials/:id/access — owner выдаёт editor другому пользователю | 200, MemorialAccess создан | ✅ | 🔴 |
| 7.1.2 | POST /memorials/:id/access — owner выдаёт viewer | 200 | ✅ | 🔴 |
| 7.1.3 | POST /memorials/:id/access — owner пытается выдать owner роль | 400/403 (запрещено) | ✅ | 🔴 |
| 7.1.4 | POST /memorials/:id/access — editor пытается выдать доступ | 403 | ✅ | 🔴 |
| 7.1.5 | POST /memorials/:id/access — выдать доступ по несуществующему email | 404 | ✅ | 🟡 |
| 7.1.6 | Повторная выдача доступа (уже есть запись) | 409 или обновляет роль | ❌ | 🟡 |

### 7.2 Изменение и отзыв доступа
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 7.2.1 | PATCH /memorials/:id/access/:userId — понизить editor до viewer | 200, роль обновлена | ✅ | 🟡 |
| 7.2.2 | PATCH — попытка понизить owner | 403 | ✅ | 🟡 |
| 7.2.3 | DELETE /memorials/:id/access/:userId — отзыв access | 200, запись удалена | ✅ | 🟡 |
| 7.2.4 | DELETE — попытка удалить последнего owner | 403 | ✅ | 🟡 |

### 7.3 Проверка прав по ролям
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 7.3.1 | VIEWER — GET /memorials/:id | 200 | ❌ | 🔴 |
| 7.3.2 | VIEWER — GET .../memories | 200 | ❌ | 🔴 |
| 7.3.3 | VIEWER — POST .../memories | 403 | ❌ | 🔴 |
| 7.3.4 | VIEWER — POST .../media/upload | 403 | ❌ | 🔴 |
| 7.3.5 | VIEWER — DELETE /memorials/:id | 403 | ❌ | 🔴 |
| 7.3.6 | EDITOR — POST .../memories | 200 | ❌ | 🔴 |
| 7.3.7 | EDITOR — PATCH /memorials/:id | 200 | ❌ | 🔴 |
| 7.3.8 | EDITOR — DELETE /memorials/:id | 403 | ❌ | 🔴 |
| 7.3.9 | EDITOR — POST /invites/.../create | 200 | ❌ | 🔴 |
| 7.3.10 | EDITOR — POST /memorials/:id/access | 403 | ❌ | 🔴 |
| 7.3.11 | Пользователь без доступа — GET приватного мемориала | 403 | ✅ | 🔴 |
| 7.3.12 | IDOR: попытка получить чужой мемориал без роли | 403 (не 404!) | ✅ | 🔴 |

### 7.4 Запросы на доступ
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 7.4.1 | POST /memorials/:id/access/request — user запрашивает доступ | 200, AccessRequest создан | ✅ | 🔴 |
| 7.4.2 | Повторный запрос — сбрасывает статус на PENDING | 200 | ✅ | 🟡 |
| 7.4.3 | GET /memorials/:id/access/requests — owner видит PENDING запросы | 200, array | ✅ | 🟡 |
| 7.4.4 | POST .../requests/:id/approve — owner одобряет | 200, MemorialAccess создан | ✅ | 🔴 |
| 7.4.5 | POST .../requests/:id/reject — owner отклоняет | 200, статус REJECTED | ✅ | 🟡 |
| 7.4.6 | Approve request → user получает роль и может читать мемориал | GET /memorials/:id → 200 | ❌ | 🔴 |
| 7.4.7 | Editor пытается просмотреть запросы | 403 | ❌ | 🟡 |

---

## Блок 8. Семейное дерево (Family Tree)

### 8.1 Создание связей
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 8.1.1 | POST /family/relationships — PARENT связь между мемориалами | 200, relationship_id | ✅ | 🔴 |
| 8.1.2 | POST /family/relationships — SPOUSE | 200 | ✅ | 🔴 |
| 8.1.3 | POST /family/relationships — SIBLING | 200 | ✅ | 🟡 |
| 8.1.4 | POST /family/relationships — EX_SPOUSE | 200 | ✅ | 🟡 |
| 8.1.5 | POST /family/relationships — CUSTOM с custom_label | 200, label сохранён | ✅ | 🟡 |
| 8.1.6 | Дублирующаяся связь (тот же memorial + related + type) | 409 или 400 | ✅ | 🟡 |
| 8.1.7 | Связь с несуществующим related_memorial_id | 404 | ✅ | 🟡 |

### 8.2 Чтение дерева
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 8.2.1 | GET /family/relationships/:id — список прямых связей | 200, edges | ✅ | 🟡 |
| 8.2.2 | GET /family/tree/:id — дерево 3 уровня | 200, nodes + edges с generation | ❌ | 🟡 |
| 8.2.3 | GET /family/full-tree/:id — расширенное дерево | 200 | ❌ | 🟡 |
| 8.2.4 | GET /family/hidden-connections/:id — скрытые связи | 200, multi-hop пути | ❌ | 🟢 |
| 8.2.5 | GET /family/clusters/:id — сетевые кластеры | 200, clusters array | ❌ | 🟢 |

### 8.3 Удаление связей
| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 8.3.1 | DELETE /family/relationships/:id — owner удаляет связь | 200 | ✅ | 🟡 |
| 8.3.2 | DELETE /family/relationships/:id — чужой пользователь | 403 | ❌ | 🟡 |

---

## Блок 9. Публичная страница мемориала

| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 9.1 | /m/:id — публичный мемориал без авторизации | страница отображается | ❌ (E2E) | 🔴 |
| 9.2 | /m/:id — приватный мемориал без авторизации | показывает кнопку "Request Access" | ❌ (E2E) | 🟡 |
| 9.3 | /m/:id — chat tab работает без авторизации | чат отвечает | ❌ (E2E) | 🟡 |
| 9.4 | /m/:id — вкладка Memories отображает карточки | список memories виден | ❌ (E2E) | 🟡 |
| 9.5 | /m/:id — Request Access flow (authenticated user) | запрос отправлен, статус PENDING | ❌ (E2E) | 🟡 |
| 9.6 | QR-код генерируется и содержит корректный URL /m/:id | URL в QR = /m/{id} | ❌ | 🟢 |

---

## Блок 10. Анимация фото

| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 10.1 | POST /ai/photo/animate — запуск (мок D-ID) | 200, task_id | ❌ | 🟡 |
| 10.2 | POST /ai/animation/status — проверка статуса | processing / done / error | ❌ | 🟡 |
| 10.3 | Статус done → is_animated=true у Media | media.is_animated обновлён | ❌ | 🟡 |

---

## Блок 11. E2E — полные пользовательские сценарии (Playwright)

### Сценарий A: Владелец создаёт мемориал с нуля
```
1. Регистрация → Login
2. Home → кнопка "Создать мемориал"
3. Заполнить форму (имя, даты, описание) → Save
4. Загрузить фото → установить как обложку
5. Добавить 2 воспоминания (текст)
6. Открыть вкладку Chat → задать вопрос → получить ответ
7. Открыть вкладку Family → добавить SPOUSE связь
8. Открыть Timeline → убедиться что memories отображаются
```
**Файл:** `e2e/tests/memorial_owner_flow.spec.js` ❌

### Сценарий B: Гость добавляет воспоминание по инвайту
```
1. Owner создаёт мемориал
2. Owner создаёт invite link (с меткой "Семья")
3. Анонимный контекст: открыть /contribute/:token
4. Ввести текст воспоминания → Submit
5. Убедиться что memory появилась в мемориале owner'а
```
**Файл:** `e2e/tests/invite.spec.js` ⚠️ (базовый тест есть, нужно расширить)

### Сценарий C: Запрос доступа и одобрение
```
1. Owner создаёт приватный мемориал
2. User2 регистрируется, открывает /m/:id
3. Видит кнопку "Request Access" → отправляет запрос
4. Owner (в другом окне) заходит в MemorialDetail → Access → видит PENDING запрос
5. Owner одобряет → роль VIEWER
6. User2 перезагружает страницу → видит мемориал
```
**Файл:** `e2e/tests/access_request.spec.js` ❌

### Сценарий D: Передача прав редактора
```
1. Owner выдаёт editor роль User2 (по email)
2. User2 логинится → видит мемориал в своём Home
3. User2 открывает MemorialDetail → добавляет memory
4. User2 загружает фото
5. User2 НЕ видит кнопки Delete/Access/Invite (owner-only)
```
**Файл:** `e2e/tests/editor_flow.spec.js` ❌

### Сценарий E: Полный RAG-цикл
```
1. Owner добавляет 3 воспоминания с разными деталями
2. Открыть Chat, задать вопрос по содержимому воспоминаний
3. Получить ответ — убедиться что answer содержит информацию из memories
4. Проверить sources в ответе API
```
**Файл:** `e2e/tests/rag_chat.spec.js` ❌

---

## Блок 12. Прочее

| # | Тест | Ожидание | Покрыт | Приоритет |
|---|------|----------|--------|-----------|
| 12.1 | GET /health/ — health check | 200, {"status": "ok"} | ✅ | 🟢 |
| 12.2 | POST /waitlist/ — email регистрация | 200 | ✅ | 🟢 |
| 12.3 | POST /waitlist/ — дублирующийся email | 409 | ✅ | 🟢 |
| 12.4 | POST /ai/transcribe — аудио → текст (мок) | 200, text | ❌ | 🟡 |
| 12.5 | GET /ai/elevenlabs/quota | 200, quota info | ❌ | 🟢 |

---

## Итоговая статистика

| Блок | Всего тестов | Покрыто (✅/⚠️) | Нужно добавить (❌) |
|------|-------------|----------------|---------------------|
| 1. Аутентификация | 12 | 7 | 5 |
| 2. Мемориалы CRUD | 16 | 6 | 10 |
| 3. Медиа | 12 | 3 | 9 |
| 4. Воспоминания | 13 | 9 | 4 |
| 5. Чат / RAG | 10 | 3 | 7 |
| 6. Инвайты | 14 | 11 | 3 |
| 7. RBAC | 20 | 10 | 10 |
| 8. Family Tree | 12 | 7 | 5 |
| 9. Публичная страница | 6 | 0 | 6 |
| 10. Анимация | 3 | 0 | 3 |
| 11. E2E сценарии | 5 | 0 | 5 |
| 12. Прочее | 5 | 3 | 2 |
| **Итого** | **128** | **59 (46%)** | **69 (54%)** |

---

## Приоритет реализации

### Фаза 1 — Критично (🔴), ~3-4 часа
Покрыть все 🔴 тесты, которых нет. Фокус:
- Права по ролям (VIEWER/EDITOR/OWNER) на все основные операции
- Публичный/приватный доступ без авторизации
- Гостевой вклад через invite_token
- Approve access request → user получает доступ

### Фаза 2 — Важно (🟡), ~4-6 часов
- Медиа upload/download (с реальными файлами)
- RAG-чат (с мок-embeddings)
- E2E сценарии A, B, C

### Фаза 3 — Желательно (🟢), ~2-3 часа
- Family tree эндпоинты (full-tree, hidden-connections)
- Анимация фото (с моком D-ID)
- E2E сценарии D, E

---

## Запуск тестов

```bash
# Backend pytest
cd backend
source .venv/bin/activate
pytest tests/ -v                          # все тесты
pytest tests/test_access.py -v            # только access control
pytest tests/ -k "role" -v               # тесты с "role" в имени
pytest tests/ --tb=short 2>&1 | head -50  # краткий вывод

# E2E Playwright
cd e2e
npx playwright test                       # все
npx playwright test invite.spec.js        # только инвайты
npx playwright test --headed              # с браузером (debug)
```
