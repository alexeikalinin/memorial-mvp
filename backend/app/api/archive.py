"""Authenticated, owner-only portable ZIP export. No secrets or other owners' archives."""
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.db import get_db, Base
from app.models import User, Memorial
from app.config import settings

router = APIRouter(prefix='/account', tags=['account'])
SECRET_PARTS = ('password', 'token', 'secret', 'google_id', 'request_hash', 'cache_key', 'code_hash', 'challenge', 'visitor_key')


def portable(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def write_media(archive, media):
    from app.api.media import _resolve_local_path
    from app.services.s3_service import get_s3_client
    path = _resolve_local_path(media['file_path'])
    root = Path(__file__).resolve().parents[2] / 'uploads'
    name = f"files/{media['memorial_id']}/{media['id']}_{Path(media['file_name']).name}"
    path = path.resolve()
    root = root.resolve()
    if path.is_relative_to(root) and path.is_file():
        archive.write(path, name)
        return
    if settings.USE_S3:
        client = get_s3_client()
        if client:
            with TemporaryFile() as file:
                client.download_fileobj(settings.S3_BUCKET_NAME, media['file_path'], file)
                file.seek(0)
                with archive.open(name, 'w') as target:
                    import shutil
                    shutil.copyfileobj(file, target)
            return
    raise ValueError('Original media unavailable')


class BrowserArchiveRequest(BaseModel):
    chats: dict[str, list[dict]] = Field(default_factory=dict)


@router.get('/export/manifest')
def export_manifest(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {'memorial_ids': [r[0] for r in db.query(Memorial.id).filter(Memorial.owner_id == user.id).all()]}


@router.post('/export')
def export_with_browser_history(payload: BrowserArchiveRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if len(json.dumps(payload.chats).encode()) > 10 * 1024 * 1024:
        raise HTTPException(413, 'История слишком большая. Используйте серверный экспорт.')
    return build_archive(db, user, payload.chats)


@router.get('/export')
def export_account(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return build_archive(db, user)


def build_archive(db, user, browser_chats=None):
    own_ids = [r[0] for r in db.query(Memorial.id).filter(Memorial.owner_id == user.id).all()]
    output = TemporaryFile()
    try:
        data = {}
        with ZipFile(output, 'w', ZIP_DEFLATED, allowZip64=True) as archive:
            for table in Base.metadata.tables.values():
                cols = table.c
                if table.name == 'users':
                    condition = cols.id == user.id
                elif table.name == 'memorials':
                    condition = cols.id.in_(own_ids)
                elif 'memorial_id' in cols:
                    condition = cols.memorial_id.in_(own_ids)
                    if 'related_memorial_id' in cols:
                        condition = condition & cols.related_memorial_id.in_(own_ids)
                elif 'memory_id' in cols:
                    from app.models import Memory
                    condition = cols.memory_id.in_(select(Memory.id).where(Memory.memorial_id.in_(own_ids)))
                elif 'user_id' in cols:
                    condition = cols.user_id == user.id
                elif 'owner_id' in cols:
                    condition = cols.owner_id == user.id
                else:
                    continue
                if table.name == 'avatar_answer_cache':
                    condition = condition & (cols.owner_id == user.id)
                if table.name in ('guest_chat_usage', 'yandex_attempts', 'yandex_tickets', 'google_web_attempts', 'google_web_tickets'):
                    continue
                rows = []
                for raw in db.execute(select(table).where(condition)).mappings():
                    row = {}
                    for key, value in raw.items():
                        if any(part in key for part in SECRET_PARTS):
                            continue
                        if isinstance(value, bytes):
                            original_name = Path(raw.get('file_name') or f'{key}.bin').name
                            file_name = f'database-files/{table.name}/{raw.get("id", raw.get("memory_id", len(rows)))}_{original_name}'
                            archive.writestr(file_name, value)
                            row[key] = {'archive_file': file_name}
                        else:
                            row[key] = portable(value)
                    rows.append(row)
                    if table.name == 'media':
                        write_media(archive, raw)
                    if table.name == 'avatar_answer_cache':
                        for entry in (raw.get('audio_variants') or {}).values():
                            filename = entry['filename'] if isinstance(entry, dict) else entry
                            from app.services.generated_audio import find_generated_audio
                            path = find_generated_audio(filename)
                            if path.is_file():
                                archive.write(path, f'answer-audio/{Path(filename).name}')
                            elif settings.USE_S3:
                                from app.services.s3_service import get_s3_client
                                with TemporaryFile() as audio:
                                    get_s3_client().download_fileobj(settings.S3_BUCKET_NAME, f'audio/{Path(filename).name}', audio)
                                    audio.seek(0)
                                    import shutil
                                    with archive.open(f'answer-audio/{Path(filename).name}', 'w') as target:
                                        shutil.copyfileobj(audio, target)
                            else:
                                raise ValueError('Saved reply audio unavailable')
                data[table.name] = rows
            browser_chats = {str(mid): browser_chats[str(mid)] for mid in own_ids if browser_chats and str(mid) in browser_chats}
            archive.writestr('browser-chat-history.json', json.dumps(browser_chats, ensure_ascii=False, indent=2))
            archive.writestr('data.json', json.dumps(data, ensure_ascii=False, indent=2, default=str))
            archive.writestr('README.txt', 'vspomin.ai archive\nAccount data and owned memorials, original media and saved answers.\nPasswords, access tokens and other owners\' private archives are excluded.\nVoice provider IDs are references, not downloadable voice model weights.\nChat history from the current browser is included when supplied by the app. Other browsers and devices are not accessible; historical chats were not stored on the server.\n')
        output.seek(0)
    except Exception:
        output.close()
        raise HTTPException(503, 'Не удалось собрать полный архив. Один из файлов недоступен. Попробуйте позже.')

    def chunks():
        try:
            while block := output.read(1024 * 1024):
                yield block
        finally:
            output.close()
    filename = 'vspomin-archive-' + datetime.now(timezone.utc).strftime('%Y-%m-%d') + '.zip'
    return StreamingResponse(chunks(), media_type='application/zip', headers={
        'Content-Disposition': f'attachment; filename="{filename}"', 'Cache-Control': 'no-store',
    })
