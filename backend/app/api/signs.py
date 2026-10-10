"""Temporary signs of memory and private owner history."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional
from sqlalchemy.orm import Session

from app.auth import get_optional_user, get_current_user, require_memorial_access, require_actual_memorial_owner
from app.config import settings
from app.db import get_db
from app.limiter import limiter
from app.models import Memorial, MemorialSign, User

router = APIRouter(prefix='/api/v1/memorials', tags=['Signs of memory'])


class SignCreate(BaseModel):
    kind: Literal['candle', 'flowers']
    variant: str
    display_name: str = Field('', max_length=80)
    comment: str = Field('', max_length=500)
    flower_type: Optional[Literal['carnations', 'roses', 'chrysanthemums', 'lilies', 'asters', 'gerberas']] = None
    flower_color: Optional[Literal['red', 'white', 'yellow', 'pink', 'purple', 'blue']] = None

    @model_validator(mode='after')
    def valid_variant(self):
        choices = {'candle': {'classic', 'taper', 'votive', 'lampada', 'lantern', 'pillar', 'beeswax', 'tea_light', 'memorial_glass', 'oil_lamp'},
                   'flowers': {'red_carnations', 'white_carnations', 'carnations', 'roses', 'chrysanthemums', 'lilies', 'asters', 'gerberas'}}
        if self.variant not in choices[self.kind]:
            raise ValueError('Invalid variant for this sign')
        if self.kind == 'candle' and (self.flower_type or self.flower_color):
            raise ValueError('Flower choices apply only to flowers')
        if self.kind == 'flowers':
            legacy_type = 'carnations' if self.variant.endswith('_carnations') else self.variant
            if self.flower_type and self.flower_type != legacy_type:
                raise ValueError('Flower type must match variant')
            self.flower_type = self.flower_type or legacy_type
            self.flower_color = self.flower_color or ('white' if self.variant == 'white_carnations' else 'red')
        self.comment = self.comment.strip()
        self.display_name = self.display_name.strip()
        return self

    class Config:
        extra = 'forbid'


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def serialize(sign):
    result = {key: getattr(sign, key) for key in
              ('id', 'kind', 'variant', 'display_name', 'comment', 'flower_type', 'flower_color')}
    result.update(created_at=utc(sign.created_at), expires_at=utc(sign.expires_at))
    return result


@router.get('/{memorial_id}/signs')
def active_signs(memorial_id: int, db: Session = Depends(get_db),
                 current_user: Optional[User] = Depends(get_optional_user)):
    require_memorial_access(memorial_id, current_user, db, allow_public=True)
    now = datetime.now(timezone.utc)
    signs = db.query(MemorialSign).filter(MemorialSign.memorial_id == memorial_id,
                                         MemorialSign.expires_at > now).order_by(MemorialSign.created_at.desc()).limit(100).all()
    candle_lit = db.query(MemorialSign.id).filter(MemorialSign.memorial_id == memorial_id,
                   MemorialSign.kind == 'candle', MemorialSign.expires_at > now).first() is not None
    return {'items': [serialize(sign) for sign in signs], 'candle_lit': candle_lit}


@router.post('/{memorial_id}/signs')
@limiter.limit('10/minute')
def leave_sign(request: Request, memorial_id: int, body: SignCreate,
               visitor: Optional[str] = Header(None, alias='X-Memorial-Visitor'),
               db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_user)):
    require_memorial_access(memorial_id, current_user, db, allow_public=True)
    if current_user:
        identity = f'user:{current_user.id}'
    else:
        try:
            identity = f'guest:{UUID(visitor or "")}'
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(400, 'A visitor identifier is required')
    key = hmac.new(settings.SECRET_KEY.encode(), identity.encode(), hashlib.sha256).hexdigest()
    # Serialize writes for one memorial on PostgreSQL to avoid duplicate active gestures.
    db.query(Memorial).filter(Memorial.id == memorial_id).with_for_update().first()
    now = datetime.now(timezone.utc)
    existing = db.query(MemorialSign).filter(MemorialSign.memorial_id == memorial_id,
                 MemorialSign.visitor_key == key, MemorialSign.kind == body.kind,
                 MemorialSign.expires_at > now).first()
    if existing:
        db.commit()
        return serialize(existing)
    sign = MemorialSign(memorial_id=memorial_id, visitor_key=key, kind=body.kind,
                        variant=body.variant, display_name=body.display_name, comment=body.comment,
                        flower_type=body.flower_type, flower_color=body.flower_color,
                        created_at=now, expires_at=now + timedelta(hours=24))
    db.add(sign)
    db.commit()
    db.refresh(sign)
    return serialize(sign)


@router.get('/{memorial_id}/signs/journal')
def signs_journal(memorial_id: int, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100),
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_actual_memorial_owner(memorial_id, current_user, db)
    query = db.query(MemorialSign).filter(MemorialSign.memorial_id == memorial_id)
    return {'total': query.count(), 'items': [serialize(sign) for sign in
            query.order_by(MemorialSign.created_at.desc(), MemorialSign.id.desc()).offset(offset).limit(limit).all()]}
