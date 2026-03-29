"""
API endpoints для управления доступом к мемориалам.
"""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_memorial_access
from app.db import get_db
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
):
    """Запросить доступ к мемориалу. Только для зарегистрированных пользователей без доступа."""
    # Проверяем что мемориал существует (404 если нет)
    from app.models import Memorial
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memorial not found")

    # Проверяем что у пользователя ещё нет доступа
    existing_access = (
        db.query(MemorialAccess)
        .filter(MemorialAccess.memorial_id == memorial_id, MemorialAccess.user_id == current_user.id)
        .first()
    )
    if existing_access:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have access to this memorial",
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
