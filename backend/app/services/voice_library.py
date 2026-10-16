"""Saved clone candidates and idempotency before any paid provider call."""
import hashlib
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models import Memorial, MemorialVoice


def preserve_current_voice(db, memorial):
    if not memorial.voice_id:
        return
    existing = db.query(MemorialVoice).filter_by(memorial_id=memorial.id, voice_id=memorial.voice_id).first()
    if not existing:
        db.add(MemorialVoice(memorial_id=memorial.id, name='Исходный голос',
                             voice_id=memorial.voice_id, provider=memorial.voice_provider or 'elevenlabs', state='ready'))
        db.flush()


def serialize_voice(row, memorial):
    return {'id': row.id, 'name': row.name, 'provider': row.provider, 'state': row.state,
            'active': row.voice_id is not None and row.voice_id == memorial.voice_id and row.provider == (memorial.voice_provider or 'elevenlabs'),
            'created_at': row.created_at.isoformat() if row.created_at else None}


def reserve_voice(db, memorial, paths, provider, name):
    # Canonical content hashes ignore filenames and file order; renaming/reordering is not a new clone.
    digests = []
    for path in paths:
        digest = hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        digests.append(digest.hexdigest())
    request_hash = hashlib.sha256((provider + ':fast:v1:' + ':'.join(sorted(digests))).encode()).hexdigest()
    # Serialize creations for one memorial on PostgreSQL, including different batches.
    db.query(Memorial).filter_by(id=memorial.id).with_for_update().one()
    preserve_current_voice(db, memorial)
    existing = db.query(MemorialVoice).filter_by(memorial_id=memorial.id, request_hash=request_hash).first()
    if existing:
        db.commit()
        if existing.state == 'ready':
            return existing, True
        raise HTTPException(status_code=409, detail='Эта попытка уже зарегистрирована. Проверьте список голосов; повторное клонирование не запущено.')
    if db.query(MemorialVoice).filter_by(memorial_id=memorial.id, state='pending').first():
        db.commit()
        raise HTTPException(status_code=409, detail='Дождитесь завершения предыдущего клонирования.')
    row = MemorialVoice(memorial_id=memorial.id, provider=provider, name=name[:255], request_hash=request_hash, state='pending')
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='Эта запись уже обрабатывается; повторное клонирование не запущено.') from exc
    return row, False
