"""
Authentication endpoints: register, login, me, Google OAuth.
"""
import urllib.parse
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, Token, TokenWithUser, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 token endpoint. The 'username' field must contain the user's email."""
    user = db.query(User).filter(User.email == form_data.username, User.is_active == True).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token({"sub": str(user.id)}))


@router.post("/login", response_model=TokenWithUser)
def login_json(body: LoginRequest, db: Session = Depends(get_db)):
    """JSON login endpoint. Returns token + user object."""
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
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
    """Редирект на Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
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
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Google OAuth callback: обменивает code на токен, создаёт/находит User, возвращает JWT."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

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
            raise HTTPException(status_code=400, detail="Failed to exchange Google code")
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        # 2. Получить профиль пользователя
        userinfo_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info")
        info = userinfo_resp.json()

    google_id = info.get("sub")
    email = info.get("email")
    name = info.get("name") or email.split("@")[0]
    avatar_url = info.get("picture")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Incomplete Google profile")

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
    return RedirectResponse(
        f"{frontend_url}/auth/callback?token={jwt_token}",
        status_code=302,
    )
