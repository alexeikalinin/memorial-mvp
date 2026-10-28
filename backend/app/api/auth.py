"""
Authentication endpoints: register, login, me, Google OAuth,
email verification, password reset.
"""
import secrets
from datetime import datetime, timedelta, timezone


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
def google_login():
    """Legacy links enter the browser-verifier flow; no unbound OAuth requests."""
    return RedirectResponse(settings.FRONTEND_URL.rstrip('/') + '/auth/google/start', status_code=302)


@router.get("/google/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None,
                          error: str | None = None, db: Session = Depends(get_db)):
    if state and state.startswith('mobile.'):
        from app.api.mobile_auth import complete
        return await complete(code, state, error, db)
    from app.api.google_web_auth import complete
    return await complete(request, code, state, error, db)


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
