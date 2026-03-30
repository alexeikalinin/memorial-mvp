"""
API для инвайт-токенов — упрощённый доступ родственников без регистрации.
"""
import secrets
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_memorial_access
from app.db import get_db
from app.models import Memorial, MemorialInvite, User, UserRole
from app.schemas import InviteCreate, InviteResponse, InviteValidateResponse
from app.config import settings

router = APIRouter(prefix="/invites", tags=["invites"])


def _make_invite_url(token: str) -> str:
    """Публичный URL инвайта; приоритет PUBLIC_FRONTEND_URL, иначе FRONTEND_URL."""
    for attr in ("PUBLIC_FRONTEND_URL", "FRONTEND_URL"):
        raw = getattr(settings, attr, None)
        if isinstance(raw, str) and raw.strip():
            return f"{raw.strip().rstrip('/')}/contribute/{token}"
    return f"http://localhost:5173/contribute/{token}"


def _invite_to_response(invite: MemorialInvite) -> InviteResponse:
    return InviteResponse(
        token=invite.token,
        label=invite.label,
        invite_url=_make_invite_url(invite.token),
        expires_at=invite.expires_at,
        uses_count=invite.uses_count,
        permissions=invite.permissions or {"add_memories": True, "chat": True, "view_media": True},
    )


@router.post("/memorials/{memorial_id}/create", response_model=InviteResponse, status_code=201)
def create_invite(
    memorial_id: int,
    data: InviteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    if not memorial:
        raise HTTPException(status_code=404, detail="Мемориал не найден")

    expires_at = None
    if data.expires_at is not None:
        expires_at = data.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    elif data.expires_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days)

    invite = MemorialInvite(
        memorial_id=memorial_id,
        token=secrets.token_urlsafe(32),
        label=data.label,
        permissions=data.permissions or {"add_memories": True, "chat": True, "view_media": True},
        expires_at=expires_at,
        uses_count=0,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _invite_to_response(invite)


@router.get("/validate/{token}", response_model=InviteValidateResponse)
def validate_invite(token: str, db: Session = Depends(get_db)):
    invite = db.query(MemorialInvite).filter(MemorialInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Ссылка недействительна")

    if invite.expires_at:
        # SQLite returns naive datetimes — compare in naive UTC
        now_utc = datetime.utcnow()
        exp = invite.expires_at
        if exp.tzinfo is not None:
            exp = exp.replace(tzinfo=None)
        if exp < now_utc:
            raise HTTPException(status_code=404, detail="Срок действия ссылки истёк")

    invite.uses_count = (invite.uses_count or 0) + 1
    db.commit()

    memorial = invite.memorial
    return InviteValidateResponse(
        memorial_id=memorial.id,
        memorial_name=memorial.name,
        cover_photo_id=memorial.cover_photo_id,
        label=invite.label,
        permissions=invite.permissions or {"add_memories": True, "chat": True, "view_media": True},
    )


@router.get("/memorials/{memorial_id}/list", response_model=List[InviteResponse])
def list_invites(
    memorial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    if not memorial:
        raise HTTPException(status_code=404, detail="Мемориал не найден")

    invites = db.query(MemorialInvite).filter(MemorialInvite.memorial_id == memorial_id).all()
    return [_invite_to_response(i) for i in invites]


@router.delete("/{token}", status_code=204)
def revoke_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invite = db.query(MemorialInvite).filter(MemorialInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Инвайт не найден")
    require_memorial_access(invite.memorial_id, current_user, db, min_role=UserRole.EDITOR)
    db.delete(invite)
    db.commit()
    return None
