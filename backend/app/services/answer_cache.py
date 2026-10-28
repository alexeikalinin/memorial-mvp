"""Exact-question cache, scoped to owner and current archive revision."""
import hashlib
import json
import re
import uuid
from pathlib import Path
from app.models import AvatarAnswerCache
from app.services.generated_audio import generated_audio_dir, find_generated_audio


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def key_for(request, memorial, memories, user):
    return digest(['v1', user.id, memorial.id, memorial.owner_id, memorial.name, memorial.description,
                   memorial.birth_date, memorial.death_date,
                   re.sub(r'\s+', ' ', request.question.strip()).casefold(), request.language,
                   request.use_persona, [(m.id, m.title, m.content, m.contributor_name) for m in sorted(memories, key=lambda m: m.id)]])


def speech_text(text, style):
    if style == 'natural':
        return re.sub(r'\n\s*\n', ' [pause] ', text)
    cues = {'calm': '[calm]', 'warm': '[warm, gentle tone]', 'happy': '[happy]', 'sad': '[sad]', 'nostalgic': '[nostalgic]'}
    cue = cues[style]
    return cue + ' ' + re.sub(r'\n\s*\n', ' [pause] ', text)


def audio_key(request, memorial):
    from app.services.voice_models import resolve_fish_model
    from app.config import settings
    model = resolve_fish_model(memorial.voice_tts_model, settings.FISH_AUDIO_MODEL)
    return digest([memorial.voice_id, memorial.voice_provider, model,
                   request.speech_speed, request.pronunciations, request.speech_style])


async def cached_response(row, request, memorial, db):
    from app.schemas import AvatarChatResponse
    from app.api.ai import _resolve_tts_voice
    from app.services.ai_tasks import generate_speech
    result = AvatarChatResponse(**row.response)
    if not request.include_audio:
        result.audio_url = None
        return result
    variant = audio_key(request, memorial)
    entry = (row.audio_variants or {}).get(variant)
    filename = entry.get('filename') if isinstance(entry, dict) else entry
    url = entry.get('url') if isinstance(entry, dict) else None
    available = filename and (find_generated_audio(filename).is_file() or (url and url.startswith('https://')))
    if available and not request.regenerate_audio:
        result.audio_url = url or '/api/v1/media/audio/' + filename
        return result
    voice_id, provider = _resolve_tts_voice(memorial)
    markup = speech_text(result.answer, request.speech_style) if provider == 'fish_audio' else result.answer
    if not request.regenerate_audio:
        row.speech_markup = {**(row.speech_markup or {}), request.speech_style: markup}
    try:
        audio = await generate_speech(markup, voice_id=voice_id, provider=provider,
                                      speed=request.speech_speed, pronunciations=request.pronunciations,
                                      model=memorial.voice_tts_model)
        filename = f'cached_{uuid.uuid4().hex}.mp3'
        path = generated_audio_dir() / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)
        entry = {'filename': filename, 'url': '/api/v1/media/audio/' + filename, 'request': request.model_dump()}
        if request.regenerate_audio:
            preview_id = uuid.uuid4().hex
            entry.update(variant=variant, request=request.model_dump(), markup=markup)
            row.audio_variants = {**(row.audio_variants or {}), 'pending:' + preview_id: entry}
            result.audio_preview_id = preview_id
            result.answer_cache_id = row.id
        else:
            row.audio_variants = {**(row.audio_variants or {}), variant: entry}
        result.audio_url = '/api/v1/media/audio/' + filename
        result.audio_error = None
    except Exception:
        result.audio_url = None
        result.audio_error = 'Не удалось создать озвучку. Попробуйте ещё раз.'
    db.commit()
    return result


def save_response(db, cache_key, request, memorial, user, result, source_ids=None):
    if not cache_key or result.suggest_memory:
        return
    row = db.query(AvatarAnswerCache).filter_by(cache_key=cache_key).first()
    if row is None:
        row = AvatarAnswerCache(cache_key=cache_key, owner_id=user.id, memorial_id=memorial.id,
                                question=request.question, response={}, speech_markup={}, audio_variants={})
        db.add(row)
    payload = result.model_dump()
    payload.update(audio_url=None, audio_error=None, animation_task_id=None, animation_provider=None)
    payload["_request"] = request.model_dump()
    payload["_source_memory_ids"] = [int(value.removeprefix("memory_")) for value in (source_ids or []) if isinstance(value, str) and value.removeprefix("memory_").isdigit()]
    row.response = payload
    row.speech_markup = {request.speech_style: speech_text(result.answer, request.speech_style)}
    if result.audio_url and (result.audio_url.startswith('/api/v1/media/audio/') or result.audio_url.startswith('https://')):
        from urllib.parse import urlparse
        filename = Path(urlparse(result.audio_url).path).name
        row.audio_variants = {audio_key(request, memorial): {'filename': filename, 'url': result.audio_url, 'request': request.model_dump()}}
    # Concurrent identical questions may finish together; preserve the winning row.
    from sqlalchemy.exc import IntegrityError
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def select_preview(db, user, cache_id, preview_id, accept):
    from fastapi import HTTPException
    from app.auth import require_actual_memorial_owner
    from app.models import Memorial, Memory
    from app.schemas import AvatarChatRequest
    row = db.query(AvatarAnswerCache).filter_by(id=cache_id, owner_id=user.id).with_for_update().first()
    if row is None:
        raise HTTPException(404, 'Audio preview not found')
    require_actual_memorial_owner(row.memorial_id, user, db)
    entries = dict(row.audio_variants or {})
    entry = entries.get('pending:' + preview_id)
    if not entry:
        raise HTTPException(404, 'Audio preview not found')
    if accept:
        memorial = db.get(Memorial, row.memorial_id)
        request = AvatarChatRequest(**entry['request'])
        memories = db.query(Memory).filter_by(memorial_id=memorial.id, status='approved').all()
        if key_for(request, memorial, memories, user) != row.cache_key or audio_key(request, memorial) != entry['variant']:
            raise HTTPException(409, 'Воспоминания или настройки голоса изменились. Создайте новый вариант.')
        entries[entry['variant']] = {'filename': entry['filename'], 'url': entry['url'], 'request': entry['request']}
        row.speech_markup = {**(row.speech_markup or {}), request.speech_style: entry['markup']}
    entries.pop('pending:' + preview_id)
    row.audio_variants = entries
    db.commit()
    if not accept:
        try:
            find_generated_audio(entry['filename']).unlink(missing_ok=True)
        except OSError:
            import logging
            logging.getLogger(__name__).warning('Could not remove discarded audio preview')
    return {'audio_url': entry['url'] if accept else None}
