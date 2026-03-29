"""
JWT authentication utilities and FastAPI dependency functions.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Memorial, MemorialAccess, User, UserRole

# auto_error=False — не бросаем 401 автоматически, обрабатываем вручную (нужно для dev-bypass)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/token",
    auto_error=False,
)

ROLE_PRIORITY = {UserRole.VIEWER: 1, UserRole.EDITOR: 2, UserRole.OWNER: 3}


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: Optional[str]) -> bool:
    if not hashed:
        return False  # Google-only users have no password
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def _get_user_from_token(token: Optional[str], db: Session) -> Optional[User]:
    """Decode JWT token and return User, or None if invalid."""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    return db.query(User).filter(User.id == int(user_id_str), User.is_active == True).first()


def _get_dev_user(db: Session) -> Optional[User]:
    """Return user id=1 in DEBUG mode (dev bypass)."""
    if settings.DEBUG:
        return db.query(User).filter(User.id == 1, User.is_active == True).first()
    return None


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Required authentication. In DEBUG mode falls back to user id=1."""
    user = _get_user_from_token(token, db) or _get_dev_user(db)
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional authentication. In DEBUG mode falls back to user id=1."""
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    return _get_user_from_token(token, db) or _get_dev_user(db)


def require_memorial_access(
    memorial_id: int,
    user: Optional[User],
    db: Session,
    min_role: UserRole = UserRole.VIEWER,
    allow_public: bool = False,
) -> Memorial:
    """
    Check user access to a memorial.
    Returns Memorial or raises 401/403/404.
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memorial not found")

    # Public memorials: allow anyone to view without auth
    if allow_public and memorial.is_public and ROLE_PRIORITY[min_role] <= ROLE_PRIORITY[UserRole.VIEWER]:
        return memorial

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access = db.query(MemorialAccess).filter(
        MemorialAccess.memorial_id == memorial_id,
        MemorialAccess.user_id == user.id,
    ).first()

    if access is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if ROLE_PRIORITY[access.role] < ROLE_PRIORITY[min_role]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return memorial
