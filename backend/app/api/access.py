"""
API endpoints для управления доступом к мемориалам.
"""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_memorial_access
from app.db import get_db
from app.i18n import get_lang, tr
from app.models import AccessRequest, AccessRequestStatus, MemorialAccess, User, UserRole
from app.schemas import (
    AccessEntryResponse,
    AccessRequestCreate,
    AccessRequestResponse,
    GrantAccessRequest,
    UpdateAccessRequest,
)

router = APIRouter(prefix="/memorials", tags=["access"])


def _access_to_response(entry: MemorialAccess) -> AccessEntryResponse:
    return AccessEntryResponse(
        id=entry.id,
        memorial_id=entry.memorial_id,
        user_id=entry.user_id,
        user_email=entry.user.email,
        user_username=entry.user.username,
        user_full_name=entry.user.full_name,
        role=entry.role.value if hasattr(entry.role, "value") else str(entry.role),
        granted_by=entry.granted_by,
        created_at=entry.created_at,
    )


@router.get("/{memorial_id}/access", response_model=List[AccessEntryResponse])
async def list_access(
    memorial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список всех пользователей с доступом к мемориалу. Только для OWNER."""
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    entries = (
        db.query(MemorialAccess)
        .filter(MemorialAccess.memorial_id == memorial_id)
        .all()
    )
    return [_access_to_response(e) for e in entries]


@router.post("/{memorial_id}/access", response_model=AccessEntryResponse, status_code=status.HTTP_201_CREATED)
async def grant_access(
    memorial_id: int,
    data: GrantAccessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Выдать доступ пользователю по email. Только для OWNER. Нельзя назначить роль owner."""
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    # Нельзя выдать роль owner через этот endpoint
    if data.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot grant owner role via this endpoint",
        )

    if data.role not in ("editor", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'editor' or 'viewer'",
        )

    target_user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Нельзя изменить собственный доступ
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own access",
        )

    existing = (
        db.query(MemorialAccess)
        .filter(
            MemorialAccess.memorial_id == memorial_id,
            MemorialAccess.user_id == target_user.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has access. Use PATCH to update role.",
        )

    role_enum = UserRole(data.role)
    entry = MemorialAccess(
        memorial_id=memorial_id,
        user_id=target_user.id,
        role=role_enum,
        granted_by=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _access_to_response(entry)


@router.patch("/{memorial_id}/access/{user_id}", response_model=AccessEntryResponse)
async def update_access(
    memorial_id: int,
    user_id: int,
    data: UpdateAccessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Изменить роль пользователя. Только для OWNER. Нельзя сделать owner."""
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    if data.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set owner role via this endpoint",
        )

    if data.role not in ("editor", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'editor' or 'viewer'",
        )

    entry = (
        db.query(MemorialAccess)
        .filter(
            MemorialAccess.memorial_id == memorial_id,
            MemorialAccess.user_id == user_id,
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access entry not found")

    # Нельзя изменить роль owner (владелец мемориала)
    if entry.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner role",
        )

    entry.role = UserRole(data.role)
    db.commit()
    db.refresh(entry)
    return _access_to_response(entry)


@router.delete("/{memorial_id}/access/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_access(
    memorial_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Отозвать доступ у пользователя. Только для OWNER. Нельзя удалить единственного OWNER."""
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    entry = (
        db.query(MemorialAccess)
        .filter(
            MemorialAccess.memorial_id == memorial_id,
            MemorialAccess.user_id == user_id,
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access entry not found")

    # Нельзя удалить единственного OWNER
    if entry.role == UserRole.OWNER:
        owner_count = (
            db.query(MemorialAccess)
            .filter(
                MemorialAccess.memorial_id == memorial_id,
                MemorialAccess.role == UserRole.OWNER,
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the only owner of a memorial",
            )

    db.delete(entry)
    db.commit()
    return None


# ── Access Requests ────────────────────────────────────────────────────────────

def _request_to_response(req: AccessRequest) -> AccessRequestResponse:
    return AccessRequestResponse(
        id=req.id,
        memorial_id=req.memorial_id,
        user_id=req.user_id,
        user_email=req.user.email,
        user_username=req.user.username,
        requested_role=req.requested_role.value if hasattr(req.requested_role, "value") else str(req.requested_role),
        message=req.message,
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        created_at=req.created_at,
    )


@router.post("/{memorial_id}/access/request", response_model=AccessRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_access(
    memorial_id: int,
    data: AccessRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Запросить доступ к мемориалу. Только для зарегистрированных пользователей без доступа."""
    # Проверяем что мемориал существует (404 если нет)
    from app.models import Memorial
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=tr(lang, "memorial_not_found"))

    # A direct private-page URL can request access without disclosing its contents.
    # Проверяем что у пользователя ещё нет доступа
    existing_access = (
        db.query(MemorialAccess)
        .filter(MemorialAccess.memorial_id == memorial_id, MemorialAccess.user_id == current_user.id)
        .first()
    )
    if existing_access and (existing_access.role != UserRole.VIEWER or data.requested_role != "editor"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=tr(lang, "already_have_access"),
        )

    if data.requested_role not in ("editor", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="requested_role must be 'editor' or 'viewer'",
        )

    # UPSERT: если уже подавал — сбросить на PENDING с новыми данными
    existing_req = (
        db.query(AccessRequest)
        .filter(AccessRequest.memorial_id == memorial_id, AccessRequest.user_id == current_user.id)
        .first()
    )
    if existing_req:
        existing_req.requested_role = UserRole(data.requested_role)
        existing_req.message = data.message
        existing_req.status = AccessRequestStatus.PENDING
        existing_req.reviewed_by = None
        existing_req.reviewed_at = None
        db.commit()
        db.refresh(existing_req)
        return _request_to_response(existing_req)

    req = AccessRequest(
        memorial_id=memorial_id,
        user_id=current_user.id,
        requested_role=UserRole(data.requested_role),
        message=data.message,
        status=AccessRequestStatus.PENDING,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _request_to_response(req)


@router.get("/{memorial_id}/access/requests", response_model=List[AccessRequestResponse])
async def list_access_requests(
    memorial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Список PENDING запросов доступа. Только для OWNER."""
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    requests = (
        db.query(AccessRequest)
        .filter(
            AccessRequest.memorial_id == memorial_id,
            AccessRequest.status == AccessRequestStatus.PENDING,
        )
        .order_by(AccessRequest.created_at)
        .all()
    )
    return [_request_to_response(r) for r in requests]


@router.post("/{memorial_id}/access/requests/{request_id}/approve", response_model=AccessEntryResponse)
async def approve_access_request(
    memorial_id: int,
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Одобрить запрос доступа. Только для OWNER. Создаёт MemorialAccess с запрошенной ролью."""
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    req = db.query(AccessRequest).filter(
        AccessRequest.id == request_id,
        AccessRequest.memorial_id == memorial_id,
    ).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found")

    if req.status != AccessRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {req.status.value}",
        )

    # Создаём или обновляем MemorialAccess
    existing = db.query(MemorialAccess).filter(
        MemorialAccess.memorial_id == memorial_id,
        MemorialAccess.user_id == req.user_id,
    ).first()

    if existing:
        if existing.role == UserRole.OWNER:
            raise HTTPException(409, "The recipient already owns this memorial")
        existing.role = req.requested_role
        existing.granted_by = current_user.id
        entry = existing
    else:
        entry = MemorialAccess(
            memorial_id=memorial_id,
            user_id=req.user_id,
            role=req.requested_role,
            granted_by=current_user.id,
        )
        db.add(entry)

    db.add(MemorialAccessEvent(memorial_id=memorial_id, actor_id=current_user.id,
                              target_user_id=req.user_id, action="access_" + req.requested_role.value))
    req.status = AccessRequestStatus.APPROVED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(entry)
    return _access_to_response(entry)


@router.post("/{memorial_id}/access/requests/{request_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_access_request(
    memorial_id: int,
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Отклонить запрос доступа. Только для OWNER."""
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    req = db.query(AccessRequest).filter(
        AccessRequest.id == request_id,
        AccessRequest.memorial_id == memorial_id,
    ).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found")

    if req.status != AccessRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {req.status.value}",
        )

    req.status = AccessRequestStatus.REJECTED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    return None


# Separate global administration from per-memorial editor/viewer sharing.
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from app.auth import is_service_owner


class SiteAdminUpdate(BaseModel):
    email: EmailStr
    is_admin: bool


def _require_service_owner(user):
    if not is_service_owner(user):
        raise HTTPException(status_code=403, detail="Only the service owner can manage administrators")


@router.get("/administration/site-admins")
def list_site_admins(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_service_owner(current_user)
    return [{"email": u.email, "is_service_owner": is_service_owner(u)} for u in db.query(User).filter(User.is_admin.is_(True)).order_by(User.id).all()]


@router.patch("/administration/site-admins")
def update_site_admin(data: SiteAdminUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_service_owner(current_user)
    target = db.query(User).filter(func.lower(User.email) == str(data.email).lower(), User.is_active.is_(True)).first()
    if not target:
        raise HTTPException(status_code=404, detail="The recipient must register first")
    if is_service_owner(target):
        raise HTTPException(status_code=400, detail="The service owner's permanent administrator rights cannot be changed")
    if data.is_admin and not target.email_verified:
        raise HTTPException(status_code=400, detail="The recipient must verify their email first")
    target.is_admin = data.is_admin
    db.commit()
    return {"email": target.email, "is_admin": target.is_admin}


# Kinship and investor demo mode never grant ownership. The recipient must accept.
from typing import Literal
from app.models import Memorial, OwnershipTransfer, MemorialAccessEvent, FamilyLinkRequest


class OwnershipTransferCreate(BaseModel):
    email: EmailStr
    keep_editor: bool = True


class OwnershipDecision(BaseModel):
    decision: Literal["accept", "reject", "cancel"]


def _transfer_response(req, db):
    m = db.get(Memorial, req.memorial_id)
    recipient = db.get(User, req.to_user_id)
    return dict(id=req.id, memorial_id=req.memorial_id, memorial_name=m.name if m else None,
                to_user_id=req.to_user_id, recipient_email=recipient.email if recipient else None,
                from_user_id=req.from_user_id, status=req.status, keep_editor=req.keep_editor)


@router.get("/ownership/transfers")
def list_ownership_transfers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import or_
    rows = db.query(OwnershipTransfer).filter(or_(OwnershipTransfer.from_user_id == current_user.id,
                                                 OwnershipTransfer.to_user_id == current_user.id)).order_by(OwnershipTransfer.id.desc()).limit(100).all()
    return [_transfer_response(r, db) for r in rows]


@router.post("/{memorial_id}/ownership/transfer", status_code=201)
def propose_ownership_transfer(memorial_id: int, data: OwnershipTransferCreate,
                               current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.query(Memorial).filter_by(id=memorial_id).with_for_update().first()
    if not m:
        raise HTTPException(404, "Memorial not found")
    if m.owner_id != current_user.id:
        raise HTTPException(403, "Only the actual owner can transfer this memorial")
    recipient = db.query(User).filter(func.lower(User.email) == str(data.email).lower(), User.is_active.is_(True)).first()
    if not recipient or not recipient.email_verified:
        raise HTTPException(400, "The recipient must register and verify their email first")
    if recipient.id == current_user.id:
        raise HTTPException(400, "You already own this memorial")
    if db.query(OwnershipTransfer).filter_by(memorial_id=memorial_id, status="pending").first():
        raise HTTPException(409, "A transfer is already pending")
    req = OwnershipTransfer(memorial_id=memorial_id, from_user_id=current_user.id,
                            to_user_id=recipient.id, keep_editor=data.keep_editor)
    db.add(req)
    db.commit()
    db.refresh(req)
    return _transfer_response(req, db)


@router.post("/ownership/transfers/{transfer_id}/respond")
def respond_ownership_transfer(transfer_id: int, data: OwnershipDecision,
                               current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = db.query(OwnershipTransfer).filter_by(id=transfer_id).with_for_update().first()
    if not req:
        raise HTTPException(404, "Transfer not found")
    permitted_user = req.from_user_id if data.decision == "cancel" else req.to_user_id
    if current_user.id != permitted_user:
        raise HTTPException(403, "Only the invited recipient can accept or reject this transfer")
    if req.status != "pending":
        raise HTTPException(409, "Transfer already reviewed")
    m = db.query(Memorial).filter_by(id=req.memorial_id).with_for_update().first()
    if not m or m.owner_id != req.from_user_id:
        raise HTTPException(409, "The owner has changed")
    if data.decision == "accept":
        if not current_user.email_verified or not current_user.is_active:
            raise HTTPException(403, "Verify your email before accepting ownership")
        entries = db.query(MemorialAccess).filter_by(memorial_id=m.id).all()
        for e in entries:
            if e.role == UserRole.OWNER:
                e.role = UserRole.EDITOR
        old = next((e for e in entries if e.user_id == req.from_user_id), None)
        if old and not req.keep_editor:
            db.delete(old)
        elif old:
            old.role = UserRole.EDITOR
        elif req.keep_editor:
            db.add(MemorialAccess(memorial_id=m.id, user_id=req.from_user_id,
                                  role=UserRole.EDITOR, granted_by=current_user.id))
        recipient = next((e for e in entries if e.user_id == req.to_user_id), None)
        if recipient:
            recipient.role = UserRole.OWNER
            recipient.granted_by = req.from_user_id
        else:
            db.add(MemorialAccess(memorial_id=m.id, user_id=req.to_user_id,
                                  role=UserRole.OWNER, granted_by=req.from_user_id))
        m.owner_id = req.to_user_id
        db.query(FamilyLinkRequest).filter(FamilyLinkRequest.status == "pending",
            (FamilyLinkRequest.memorial_id == m.id) | (FamilyLinkRequest.related_memorial_id == m.id)).update({"status": "cancelled"}, synchronize_session=False)
        db.add(MemorialAccessEvent(memorial_id=m.id, actor_id=current_user.id,
                                  target_user_id=current_user.id, action="ownership_transferred"))
    req.status = {"accept": "accepted", "reject": "rejected", "cancel": "cancelled"}[data.decision]
    req.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    return _transfer_response(req, db)
