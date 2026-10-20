"""Isolated Google handoff for native clients; the web OAuth URL remains unchanged."""
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.auth import create_access_token
from app.config import settings
from app.db import get_db
from app.limiter import limiter
from app.mobile_auth_models import MobileGoogleAttempt
from app.models import User
from app.schemas import UserResponse

router = APIRouter(prefix='/auth/mobile/google', tags=['mobile-auth'])
RETURN_URI = 'vspomin://oauth/callback'


class StartGoogle(BaseModel):
    challenge: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')


class ExchangeGoogle(BaseModel):
    attempt_id: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    code: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    verifier: str = Field(min_length=43, max_length=128, pattern=r'^[A-Za-z0-9._~-]+$')


def callback_uri():
    return f"{(settings.PUBLIC_API_URL or 'http://localhost:8000').rstrip('/')}{settings.API_V1_PREFIX}/auth/google/callback"


@router.post('/start')
@limiter.limit('20/minute')
def start(request: Request, data: StartGoogle, db: Session = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(501, 'Вход через Google пока не настроен на сервере.')
    now = datetime.utcnow()
    db.query(MobileGoogleAttempt).filter(MobileGoogleAttempt.expires_at < now).delete(synchronize_session=False)
    attempt = MobileGoogleAttempt(id=secrets.token_urlsafe(32), challenge=data.challenge,
                                  expires_at=now + timedelta(minutes=5), status='pending')
    db.add(attempt)
    db.commit()
    state = 'mobile.' + jwt.encode({'aud':'mobile-google', 'kind':'mobile-google',
        'attempt':attempt.id,
        'exp':datetime.now(timezone.utc)+timedelta(minutes=5)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
        'client_id':settings.GOOGLE_CLIENT_ID, 'redirect_uri':callback_uri(),
        'response_type':'code', 'scope':'openid email profile', 'prompt':'select_account', 'state':state})
    return JSONResponse({'attempt_id':attempt.id, 'authorization_url':url, 'expires_in':300},headers={'Cache-Control':'no-store'})


def _completion(attempt_id: str, code: str | None):
    params = {'attempt':attempt_id, 'code':code} if code else {'attempt':attempt_id,'error':'google_sign_in_failed'}
    return RedirectResponse(RETURN_URI+'?'+urlencode(params),status_code=302,
        headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer'})


def _google_user(db: Session, info: dict):
    google_id, email = info.get('sub'), info.get('email')
    if not isinstance(google_id,str) or not google_id or not isinstance(email,str) or '@' not in email or info.get('email_verified') is not True:
        raise HTTPException(400,'Google не подтвердил адрес электронной почты.')
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user and user.google_id and user.google_id != google_id:
            raise HTTPException(409,'Этот аккаунт связан с другим профилем Google.')
        if not user:
            base = email.split('@')[0][:180]
            username = base
            count = 0
            while db.query(User).filter(User.username == username).first():
                count += 1
                username = f'{base}{count}'
            user = User(email=email,username=username,full_name=info.get('name') or base,is_active=True)
            db.add(user)
        user.google_id = google_id
        user.avatar_url = info.get('picture')
    if not user.is_active:
        raise HTTPException(403,'Аккаунт отключён.')
    user.email_verified = True
    db.flush()
    return user


async def complete(code: str | None, state: str, error: str | None, db: Session):
    try:
        claims = jwt.decode(state.removeprefix('mobile.'),settings.SECRET_KEY,
                            algorithms=[settings.ALGORITHM],audience='mobile-google')
        if claims.get('kind') != 'mobile-google':
            raise JWTError('invalid state type')
    except JWTError:
        raise HTTPException(400,'Недействительная или устаревшая попытка входа.')
    attempt_id = claims.get('attempt')
    attempt = db.query(MobileGoogleAttempt).filter_by(id=attempt_id).first()
    if not attempt or attempt.expires_at < datetime.utcnow() or attempt.status != 'pending':
        raise HTTPException(400,'Попытка входа завершена или истекла.')
    claimed = db.query(MobileGoogleAttempt).filter_by(id=attempt_id,status='pending').update({'status':'processing'})
    db.commit()
    if claimed != 1:
        raise HTTPException(400,'Эта попытка входа уже использована.')
    if error or not code:
        db.query(MobileGoogleAttempt).filter_by(id=attempt_id).update({'status':'failed'})
        db.commit()
        return _completion(attempt_id,None)
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token = await client.post('https://oauth2.googleapis.com/token',data={
                'code':code,'client_id':settings.GOOGLE_CLIENT_ID,'client_secret':settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri':callback_uri(),'grant_type':'authorization_code'})
            if token.status_code != 200 or not token.json().get('access_token'):
                raise HTTPException(400,'Google не завершил вход.')
            profile = await client.get('https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization':'Bearer '+token.json()['access_token']})
            if profile.status_code != 200:
                raise HTTPException(400,'Не удалось получить профиль Google.')
            user = _google_user(db,profile.json())
        handoff = secrets.token_urlsafe(32)
        db.query(MobileGoogleAttempt).filter_by(id=attempt_id,status='processing').update({'status':'ready','user_id':user.id,'code_hash':hashlib.sha256(handoff.encode()).hexdigest()})
        db.commit()
    except (HTTPException,httpx.HTTPError,ValueError,TypeError,SQLAlchemyError):
        db.rollback()
        db.query(MobileGoogleAttempt).filter_by(id=attempt_id).update({'status':'failed'})
        db.commit()
        return _completion(attempt_id,None)
    return _completion(attempt_id,handoff)


@router.post('/exchange')
@limiter.limit('90/minute')
def exchange(request: Request, data: ExchangeGoogle, db: Session = Depends(get_db)):
    attempt = db.query(MobileGoogleAttempt).filter_by(id=data.attempt_id).first()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(data.verifier.encode()).digest()).decode().rstrip('=')
    if not attempt or attempt.expires_at < datetime.utcnow() or not secrets.compare_digest(challenge,attempt.challenge):
        raise HTTPException(400,'Попытка входа недействительна или истекла. Повторите вход.')
    if attempt.status != 'ready' or not attempt.code_hash or not secrets.compare_digest(hashlib.sha256(data.code.encode()).hexdigest(),attempt.code_hash):
        raise HTTPException(400,'Вход не завершён. Попробуйте ещё раз.')
    user = db.query(User).filter_by(id=attempt.user_id,is_active=True).first()
    if not user:
        raise HTTPException(403,'Аккаунт недоступен.')
    consumed = db.query(MobileGoogleAttempt).filter_by(id=attempt.id,status='ready').update({'status':'used'})
    db.commit()
    if consumed != 1:
        raise HTTPException(400,'Попытка входа уже использована.')
    return JSONResponse({'access_token':create_access_token({'sub':str(user.id)}),'token_type':'bearer',
        'user':UserResponse.model_validate(user).model_dump(mode='json')},headers={'Cache-Control':'no-store'})
