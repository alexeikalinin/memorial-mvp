# Голосовые аватары — как устроено и как починить

> Протестировано и подтверждено рабочим: 2026-03-16

## Что делает фича

Аватар отвечает голосом через ElevenLabs TTS.
- Мужской мемориал (`voice_gender=male`) → мужской голос
- Женский мемориал (`voice_gender=female`) → женский голос
- Если у мемориала загружен клон голоса (`voice_id`) → используется он

---

## Конфигурация (.env)

```env
ELEVENLABS_API_KEY=sk_5436b55841adcecd1ee83b15714b18286648be01f12124ed
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB          # дефолтный (мужской)
ELEVENLABS_VOICE_ID_MALE=pNInz6obpgDQGcFmaJgB     # Adam — мужской
ELEVENLABS_VOICE_ID_FEMALE=EXAVITQu4vr4xnSDxMaL   # Bella — женский
```

---

## Где живёт логика (бэкенд)

**`backend/app/api/ai.py`, строки ~459–500**

```python
if request.include_audio:
    if memorial.voice_id:
        voice_id = memorial.voice_id                          # клон голоса
    elif memorial.voice_gender == 'male':
        voice_id = settings.ELEVENLABS_VOICE_ID_MALE         # мужской
    elif memorial.voice_gender == 'female':
        voice_id = settings.ELEVENLABS_VOICE_ID_FEMALE       # женский
    else:
        voice_id = settings.ELEVENLABS_VOICE_ID              # дефолт

    audio_bytes = await generate_speech_elevenlabs(answer, voice_id=voice_id)
    # сохраняет в uploads/audio/ или Supabase S3
    # возвращает audio_url в ответе
```

**`backend/app/services/ai_tasks.py`** — функция `generate_speech_elevenlabs(text, voice_id)`

**`backend/app/schemas.py`**:
```python
class AvatarChatRequest:
    include_audio: bool = False   # <-- ВАЖНО: именно include_audio, не generate_audio
```

**`backend/app/config.py`, строки ~43–53** — переменные `ELEVENLABS_VOICE_ID_MALE/FEMALE`

---

## Где живёт логика (фронтенд)

**`frontend/src/components/AvatarChat.jsx`**

```js
// Отправка запроса — строка ~218
include_audio: includeAudio,   // <-- поле называется include_audio

// Получение ответа — строки ~223–236
let audioUrl = response.data.audio_url || null
// s3:// URL фильтруется, относительный путь дополняется базой
```

```js
// Рендер аудиоплеера — строки ~493–506
{getPlayableAudioUrl(msg.audioUrl) ? (
  <audio src={getPlayableAudioUrl(msg.audioUrl)} ... />
) : msg.audioError ? (
  <div>Аудио не сгенерировано: {msg.audioError}</div>
)}
```

**Функция `getPlayableAudioUrl`** (строка ~47):
- Если URL начинается с `s3://` → `null` (не воспроизводится)
- Если нет протокола и нет `/` → добавляет `/api/v1/media/audio/`
- Иначе возвращает как есть

---

## База данных

Таблица `memorials`:
- `voice_gender` (VARCHAR 20) — `'male'` или `'female'`
- `voice_id` (VARCHAR 255) — ID клона голоса ElevenLabs (опционально)

В `seed_extended.py` каждый мемориал задаётся с `voice_gender`:
```python
dict(key="vasily", name="Василий...", voice_gender="male", ...)
dict(key="pelagея", name="Пелагея...", voice_gender="female", ...)
```

---

## Как проверить что работает

```bash
# Мужской аватар — должен вернуть audio_url
curl -s -X POST "http://localhost:8000/api/v1/ai/avatar/chat" \
  -H "Content-Type: application/json" \
  -d '{"memorial_id": 1, "question": "Кто ты?", "include_audio": true}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('audio_url:', d['audio_url'])"

# Женский аватар — должен вернуть audio_url с другим файлом
curl -s -X POST "http://localhost:8000/api/v1/ai/avatar/chat" \
  -H "Content-Type: application/json" \
  -d '{"memorial_id": 2, "question": "Кто ты?", "include_audio": true}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('audio_url:', d['audio_url'])"
```

Ожидаемый результат: оба запроса возвращают `audio_url` (не null), URL-ы содержат разные имена файлов.

---

## Типичные поломки и как чинить

| Симптом | Причина | Решение |
|---|---|---|
| `audio_url: null`, `audio_error: null` | Фронт отправляет `generate_audio` вместо `include_audio` | Проверить `AvatarChat.jsx` ~218: поле должно быть `include_audio` |
| `audio_url: null`, `audio_error: "..."` | ElevenLabs API ошибка | Проверить ключ в `.env`, квоту на [elevenlabs.io](https://elevenlabs.io) |
| Оба пола одним голосом | `ELEVENLABS_VOICE_ID_MALE/FEMALE` не заданы в `.env` | Добавить оба ключа в `.env` |
| Аудио генерируется, но не воспроизводится | `audio_url` содержит `s3://` путь | Проверить `settings.supabase_public_url` в config.py; функция `getPlayableAudioUrl` фильтрует s3:// |
| `voice_gender` не определяется | Поле отсутствует в схеме БД | Удалить `memorial.db` и пересоздать: `rm memorial.db` + перезапуск бэкенда |
