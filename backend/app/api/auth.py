"""
Authentication endpoints: register, login, me, Google OAuth,
email verification, password reset.
"""
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import settings
from app.db import get_db
from app.i18n import get_lang, tr
from app.limiter import limiter
from app.models import User
from app.schemas import (
    LoginRequest, PasswordResetConfirm, PasswordResetRequest,
    Token, TokenWithUser, UserCreate, UserResponse,
)
from app.services.email_service import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db), lang: str = Depends(get_lang)):
    """Register a new user."""
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail=tr(lang, "email_taken"))
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail=tr(lang, "username_taken"))

    verification_token = secrets.token_urlsafe(32)
    token_expires = datetime.now(timezone.utc) + timedelta(hours=24)

    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send verification email (non-blocking — failure doesn't break registration)
    send_verification_email(user.email, verification_token, user.full_name or user.username, lang=lang)

    return user


@router.post("/token", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login_oauth2(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), lang: str = Depends(get_lang)):
    """OAuth2 token endpoint. The 'username' field must contain the user's email."""
    user = db.query(User).filter(User.email == form_data.username, User.is_active == True).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=tr(lang, "incorrect_credentials"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token({"sub": str(user.id)}))


@router.post("/login", response_model=TokenWithUser)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login_json(request: Request, body: LoginRequest, db: Session = Depends(get_db), lang: str = Depends(get_lang)):
    """JSON login endpoint. Returns token + user object."""
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=tr(lang, "incorrect_credentials"),
        )
    token = create_access_token({"sub": str(user.id)})
    return TokenWithUser(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
def google_login(lang: str = Depends(get_lang)):
    """Редирект на Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail=tr(lang, "google_oauth_not_configured"))
    redirect_uri = f"{settings.API_V1_PREFIX}/auth/google/callback"
    # Используем PUBLIC_API_URL если задан (prod), иначе localhost
    base = settings.PUBLIC_API_URL or "http://localhost:8000"
    params = urllib.parse.urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{base}{redirect_uri}",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse(f"{_GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db), lang: str = Depends(get_lang)):
    """Google OAuth callback: обменивает code на токен, создаёт/находит User, возвращает JWT."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail=tr(lang, "google_oauth_not_configured"))

    base = settings.PUBLIC_API_URL or "http://localhost:8000"
    redirect_uri = f"{base}{settings.API_V1_PREFIX}/auth/google/callback"

    # 1. Обменять code на access_token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(_GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=tr(lang, "google_code_exchange_failed"))
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        # 2. Получить профиль пользователя
        userinfo_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=tr(lang, "google_userinfo_failed"))
        info = userinfo_resp.json()

    google_id = info.get("sub")
    email = info.get("email")
    name = info.get("name") or email.split("@")[0]
    avatar_url = info.get("picture")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail=tr(lang, "google_incomplete_profile"))

    # 3. Найти или создать пользователя
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        # Проверить, есть ли юзер с таким email (регистрировался ранее)
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Привязать google_id к существующему аккаунту
            user.google_id = google_id
            user.avatar_url = avatar_url
        else:
            # Создать нового пользователя
            username_base = email.split("@")[0]
            username = username_base
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{username_base}{counter}"
                counter += 1
            user = User(
                email=email,
                username=username,
                full_name=name,
                hashed_password=None,
                google_id=google_id,
                avatar_url=avatar_url,
                is_active=True,
            )
            db.add(user)
        db.commit()
        db.refresh(user)

    # 4. Выдать JWT и редиректнуть на фронт
    jwt_token = create_access_token({"sub": str(user.id)})
    frontend_url = settings.FRONTEND_URL or "http://localhost:5173"
    # Google users are considered verified automatically
    if not user.email_verified:
        user.email_verified = True
        db.commit()
    return RedirectResponse(
        f"{frontend_url}/auth/callback?token={jwt_token}",
        status_code=302,
    )


# ── Email Verification ────────────────────────────────────────────────────────

@router.post("/verify-email", status_code=200)
@limiter.limit("10/minute")
def verify_email(request: Request, token: str, db: Session = Depends(get_db), lang: str = Depends(get_lang)):
    """Verify email address using token from the verification email."""
    now = datetime.now(timezone.utc)
    user = db.query(User).filter(User.verification_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail=tr(lang, "verification_token_invalid"))
    if user.email_verified:
        return {"message": tr(lang, "email_already_verified")}
    expires = user.verification_token_expires
    if expires:
        # SQLite returns naive datetimes; make comparison tz-safe
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            raise HTTPException(status_code=400, detail=tr(lang, "verification_token_expired"))

    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    return {"message": tr(lang, "email_verified_success")}


@router.post("/resend-verification", status_code=200)
@limiter.limit("3/minute")
def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Resend email verification link to the current user."""
    if current_user.email_verified:
        return {"message": tr(lang, "email_already_verified")}

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    current_user.verification_token = token
    current_user.verification_token_expires = expires
    db.commit()

    send_verification_email(current_user.email, token, current_user.full_name or current_user.username, lang=lang)
    return {"message": tr(lang, "verification_email_sent")}


# ── Password Reset ────────────────────────────────────────────────────────────

@router.post("/password-reset", status_code=200)
@limiter.limit("5/minute")
def request_password_reset(
    request: Request,
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Request a password reset link. Always returns 200 to prevent email enumeration."""
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if user:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        user.password_reset_token = token
        user.password_reset_token_expires = expires
        db.commit()
        send_password_reset_email(user.email, token, user.full_name or user.username, lang=lang)
    # Always return 200 regardless (security: don't reveal if email exists)
    return {"message": tr(lang, "password_reset_email_sent")}


@router.post("/password-reset/confirm", status_code=200)
@limiter.limit("10/minute")
def confirm_password_reset(
    request: Request,
    body: PasswordResetConfirm,
    db: Session = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Set a new password using the reset token."""
    now = datetime.now(timezone.utc)
    user = db.query(User).filter(User.password_reset_token == body.token).first()

    if not user:
        raise HTTPException(status_code=400, detail=tr(lang, "reset_token_invalid"))
    reset_expires = user.password_reset_token_expires
    if reset_expires:
        # SQLite returns naive datetimes; make comparison tz-safe
        if reset_expires.tzinfo is None:
            reset_expires = reset_expires.replace(tzinfo=timezone.utc)
        if reset_expires < now:
            raise HTTPException(status_code=400, detail=tr(lang, "reset_token_expired"))

    user.hashed_password = hash_password(body.new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    # Отзываем все JWT, выпущенные до смены пароля (на случай компрометации старого пароля/токена)
    user.tokens_invalid_before = now
    db.commit()
    return {"message": tr(lang, "password_updated_success")}
