"""Owner-curated examples. Guest reads never call LLM/TTS or expose private cache."""
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth import get_optional_authenticated_user, require_actual_memorial_owner
from app.db import get_db
from app.models import AvatarAnswerCache, FeaturedAvatarAnswer, Memorial, MemorialInvite, Memory, User
from app.schemas import AvatarChatRequest
from app.services.answer_cache import digest, key_for, audio_key

def no_cache(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix='/featured-answers', tags=['featured answers'], dependencies=[Depends(no_cache)])


def authenticated(user: Optional[User] = Depends(get_optional_authenticated_user)):
    if user is None:
        raise HTTPException(401, 'Authentication required')
    return user


def revision(memorial, memories):
    return digest([memorial.owner_id, memorial.name, memorial.description, memorial.birth_date,
                   memorial.death_date, memorial.voice_id, memorial.voice_provider, memorial.voice_tts_model,
                   [(m.id, m.title, m.content, m.contributor_name, m.event_date) for m in sorted(memories, key=lambda x: x.id)]])


def context(db, memorial_id):
    memorial = db.get(Memorial, memorial_id)
    if not memorial:
        raise HTTPException(404, 'Memorial not found')
    memories = db.query(Memory).filter_by(memorial_id=memorial_id, status='approved').all()
    return memorial, memories


def fresh(row, memorial, memories, db):
    owner = db.get(User, row.owner_id)
    if not owner or not owner.is_active:
        return False
    try:
        require_actual_memorial_owner(memorial.id, owner, db)
    except HTTPException:
        return False
    metadata = (row.response or {}).get('_request')
    requests = [metadata] if metadata else [dict(language=lang) for lang in ('ru', 'en')]
    for data in requests:
        try:
            request = AvatarChatRequest(**{**data, 'memorial_id': memorial.id, 'question': row.question})
            if not request.include_family_memories and key_for(request, memorial, memories, owner) == row.cache_key:
                return True
        except (ValueError, TypeError):
            continue
    return False


def guest_access(db, memorial, token):
    if token:
        invite = db.query(MemorialInvite).filter_by(token=token, memorial_id=memorial.id).first()
        if (not invite or not (invite.permissions or {}).get('chat') or
                (invite.expires_at and (invite.expires_at.replace(tzinfo=timezone.utc) if invite.expires_at.tzinfo is None else invite.expires_at.astimezone(timezone.utc)) <= datetime.now(timezone.utc))):
            raise HTTPException(403, 'Invalid or expired chat invitation')
    elif not memorial.is_public:
        raise HTTPException(403, 'Chat invitation required')


def audio_entry(row, variant):
    if not variant or variant.startswith('pending:'):
        return None
    entry = (row.audio_variants or {}).get(variant)
    if not isinstance(entry, dict):
        return None
    filename = entry.get('filename', '')
    from app.api.media import UPLOAD_DIR
    from app.services.generated_audio import find_generated_audio
    path = find_generated_audio(filename, UPLOAD_DIR / 'audio')
    if not filename or Path(filename).name != filename or not path.is_file():
        return None
    return path


def public_item(feature, row, token=None):
    from urllib.parse import urlencode
    suffix = '?' + urlencode({'invite_token': token}) if token else ''
    return {'id': feature.id, 'question': row.question, 'answer': row.response['answer'],
            'audio_url': f'/api/v1/featured-answers/{feature.id}/audio{suffix}' if audio_entry(row, feature.audio_variant) else None}


@router.get('/memorials/{memorial_id}/saved')
def saved(memorial_id: int, db: Session = Depends(get_db), user: User = Depends(authenticated)):
    require_actual_memorial_owner(memorial_id, user, db)
    memorial, memories = context(db, memorial_id)
    features = {f.cache_id: f for f in db.query(FeaturedAvatarAnswer).filter_by(memorial_id=memorial_id)}
    output = []
    for row in db.query(AvatarAnswerCache).filter_by(memorial_id=memorial_id, owner_id=user.id).order_by(AvatarAnswerCache.id.desc()):
        feature = features.get(row.id)
        valid = fresh(row, memorial, memories, db)
        variants = []
        for key, entry in (row.audio_variants or {}).items():
            path = audio_entry(row, key)
            if not path:
                continue
            settings = entry.get('request') or row.response.get('_request') or {}
            if not entry.get('request'):
                for style in ('natural', 'calm', 'warm', 'happy', 'sad', 'nostalgic'):
                    candidate = AvatarChatRequest(**{**settings, 'question': row.question, 'memorial_id': memorial.id, 'speech_style': style})
                    if audio_key(candidate, memorial) == key:
                        settings = candidate.model_dump()
                        break
            variants.append({'key': key, 'audio_url': f'/api/v1/media/audio/{path.name}', 'generation_settings': settings})
        output.append({'cache_id': row.id, 'question': row.question, 'answer': row.response.get('answer', ''),
                       'sources': row.response.get('sources', []), 'source_memory_ids': row.response.get('_source_memory_ids') or sorted({int(value) for source in row.response.get('sources', []) for value in re.findall(r'#(\d+)', source)} & {m.id for m in memories}),
                       'generation_settings': row.response.get('_request', {}),
                       'audio_variants': variants, 'featured': feature is not None,
                       'position': feature.position if feature else None,
                       'audio_variant': feature.audio_variant if feature else None,
                       'stale': not valid or bool(feature and feature.revision != revision(memorial, memories))})
    return output


class Selection(BaseModel):
    publish_to_guests: bool
    audio_variant: Optional[str] = None
    position: int = Field(default=0, ge=0, le=4)


@router.put('/saved/{cache_id}')
def select(cache_id: int, body: Selection, db: Session = Depends(get_db), user: User = Depends(authenticated)):
    row = db.get(AvatarAnswerCache, cache_id)
    if not row:
        raise HTTPException(404, 'Saved answer not found')
    require_actual_memorial_owner(row.memorial_id, user, db)
    if row.owner_id != user.id:
        raise HTTPException(403, 'Only your saved answers can be published')
    # Serialize the five-item limit on PostgreSQL.
    db.query(Memorial).filter_by(id=row.memorial_id).with_for_update().one()
    feature = db.query(FeaturedAvatarAnswer).filter_by(cache_id=cache_id).first()
    if not body.publish_to_guests:
        if feature:
            db.delete(feature)
        db.commit()
        return {'featured': False}
    memorial, memories = context(db, row.memorial_id)
    if not fresh(row, memorial, memories, db) or row.response.get('suggest_memory'):
        raise HTTPException(409, 'Ответ устарел. Задайте вопрос снова и проверьте ответ.')
    if body.audio_variant and not audio_entry(row, body.audio_variant):
        raise HTTPException(422, 'Selected audio is unavailable')
    if not feature:
        if db.query(FeaturedAvatarAnswer).filter_by(memorial_id=memorial.id).count() >= 5:
            raise HTTPException(409, 'Можно выбрать не более пяти вопросов')
        feature = FeaturedAvatarAnswer(memorial_id=memorial.id, cache_id=row.id)
        db.add(feature)
    feature.revision = revision(memorial, memories)
    others = db.query(FeaturedAvatarAnswer).filter(FeaturedAvatarAnswer.memorial_id == memorial.id).order_by(FeaturedAvatarAnswer.position, FeaturedAvatarAnswer.id).all()
    others = [item for item in others if item.cache_id != row.id]
    others.insert(min(body.position, len(others)), feature)
    for index, item in enumerate(others):
        item.position = index
    feature.audio_variant = body.audio_variant
    db.commit()
    return {'featured': True}


@router.get('/memorials/{memorial_id}/guest')
def guest_list(memorial_id: int, invite_token: Optional[str] = Query(None), db: Session = Depends(get_db)):
    memorial, memories = context(db, memorial_id)
    guest_access(db, memorial, invite_token)
    current = revision(memorial, memories)
    results = []
    for feature in db.query(FeaturedAvatarAnswer).filter_by(memorial_id=memorial_id).order_by(FeaturedAvatarAnswer.position, FeaturedAvatarAnswer.id):
        row = db.get(AvatarAnswerCache, feature.cache_id)
        if row and feature.revision == current and fresh(row, memorial, memories, db):
            results.append(public_item(feature, row, invite_token))
    return results


@router.get('/{feature_id}/audio')
def audio(feature_id: int, invite_token: Optional[str] = Query(None), db: Session = Depends(get_db)):
    feature = db.get(FeaturedAvatarAnswer, feature_id)
    if not feature:
        raise HTTPException(404, 'Audio not found')
    available = guest_list(feature.memorial_id, invite_token, db)
    if not any(item['id'] == feature_id for item in available):
        raise HTTPException(404, 'Audio no longer available')
    path = audio_entry(db.get(AvatarAnswerCache, feature.cache_id), feature.audio_variant)
    if not path:
        raise HTTPException(404, 'Audio not found')
    return FileResponse(path, media_type='audio/mpeg', headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})


def repeated_guest_answer(db, memorial, question, token):
    normalized = lambda text: re.sub(r'\s+', ' ', text.strip()).casefold()
    return next((item for item in guest_list(memorial.id, token, db)
                 if normalized(item['question']) == normalized(question)), None)
