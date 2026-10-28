"""Authorization-code + PKCE login. Never returns provider tokens to the browser."""
import base64
import hashlib
import re
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import _get_user_from_token, create_access_token
from app.config import settings
from app.db import get_db
from app.limiter import limiter
from app.models import User
from app.yandex_auth_models import YandexIdentity, YandexAttempt, YandexTicket

router = APIRouter(prefix='/auth/yandex', tags=['auth'])
COOKIE = 'yandex_browser'
COOKIE_PATH = settings.API_V1_PREFIX + '/auth/yandex'


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def challenge(value):
    return base64.urlsafe_b64encode(hashlib.sha256(value.encode()).digest()).rstrip(b'=').decode()


def frontend():
    return settings.FRONTEND_URL.rstrip('/')


def callback_uri():
    return (settings.PUBLIC_API_URL or 'http://localhost:8000').rstrip('/') + COOKIE_PATH + '/callback'


def configured():
    return bool(settings.YANDEX_CLIENT_ID and settings.YANDEX_CLIENT_SECRET)


def finish(error=None, ticket=None):
    params = {'yandex_error': error} if error else {'yandex_code': ticket}
    response = RedirectResponse(frontend() + '/auth/yandex/callback#' + urlencode(params), status_code=302)
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


def revoked(user, issued_at):
    cutoff = user.tokens_invalid_before
    return cutoff is not None and cutoff.replace(tzinfo=None) > issued_at


class StartRequest(BaseModel):
    challenge: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    link: bool = False


class ExchangeRequest(BaseModel):
    code: str = Field(min_length=32, max_length=128)
    verifier: str = Field(pattern=r'^[A-Za-z0-9_-]{43,128}$')


@router.get('/status')
def status():
    return {'enabled': configured()}


@router.get('/connection')
def connection(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get('authorization', '').removeprefix('Bearer ')
    user = _get_user_from_token(token, db)
    if not user:
        raise HTTPException(401, 'Authentication required')
    return {'connected': db.query(YandexIdentity).filter_by(user_id=user.id).first() is not None}


@router.post('/start')
@limiter.limit('10/minute')
def start(request: Request, payload: StartRequest, db: Session = Depends(get_db)):
    if not configured():
        raise HTTPException(503, 'Yandex sign-in is not configured')
    user = None
    if payload.link:
        token = request.headers.get('authorization', '').removeprefix('Bearer ')
        user = _get_user_from_token(token, db)
        if not user:
            raise HTTPException(401, 'Authentication required')
    now = datetime.utcnow()
    db.query(YandexAttempt).filter(YandexAttempt.expires_at < now).delete()
    db.query(YandexTicket).filter(YandexTicket.expires_at < now).delete()
    state, browser, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    db.add(YandexAttempt(state_hash=digest(state), browser_hash=digest(browser),
                         provider_verifier=verifier, frontend_challenge=payload.challenge,
                         user_id=user.id if user else None, started_at=now,
                         expires_at=now + timedelta(minutes=10)))
    db.commit()
    url = 'https://oauth.yandex.ru/authorize?' + urlencode({
        'response_type': 'code', 'client_id': settings.YANDEX_CLIENT_ID,
        'redirect_uri': callback_uri(), 'scope': 'login:email login:info',
        'state': state, 'code_challenge': challenge(verifier),
        'code_challenge_method': 'S256', 'force_confirm': 'yes',
    })
    response = JSONResponse({'url': url}, headers={'Cache-Control': 'no-store'})
    response.set_cookie(COOKIE, browser, max_age=600, path=COOKIE_PATH,
                        httponly=True, secure=callback_uri().startswith('https://'), samesite='lax')
    return response


@router.get('/callback')
async def callback(request: Request, code: str | None = None, state: str | None = None,
                   error: str | None = None, db: Session = Depends(get_db)):
    if not configured():
        return finish(error='unavailable')
    attempt = db.get(YandexAttempt, digest(state or ''))
    browser = request.cookies.get(COOKIE, '')
    if not attempt or attempt.expires_at < datetime.utcnow() or not browser or not secrets.compare_digest(attempt.browser_hash, digest(browser)):
        return finish(error='expired')
    # Atomic consumption before making a provider request, including cancellation.
    values = (attempt.provider_verifier, attempt.frontend_challenge, attempt.user_id, attempt.started_at)
    count = db.query(YandexAttempt).filter_by(state_hash=attempt.state_hash).delete()
    db.commit()
    if count != 1:
        return finish(error='expired')
    verifier, frontend_challenge, link_user_id, started_at = values
    if error or not code:
        return finish(error='cancelled')
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post('https://oauth.yandex.ru/token', data={
                'grant_type': 'authorization_code', 'code': code,
                'client_id': settings.YANDEX_CLIENT_ID, 'client_secret': settings.YANDEX_CLIENT_SECRET,
                'code_verifier': verifier, 'redirect_uri': callback_uri(),
            })
            if token_response.status_code != 200:
                return finish(error='provider')
            access_token = token_response.json().get('access_token')
            if not isinstance(access_token, str) or not access_token:
                return finish(error='provider')
            profile = await client.get('https://login.yandex.ru/info', params={'format': 'json'},
                                       headers={'Authorization': 'OAuth ' + access_token})
            if profile.status_code != 200:
                return finish(error='provider')
            info = profile.json()
        subject, email = info.get('id'), info.get('default_email')
        if not isinstance(subject, str) or not subject or len(subject) > 255:
            return finish(error='profile')
        if info.get('client_id') != settings.YANDEX_CLIENT_ID:
            return finish(error='profile')
        identity = db.get(YandexIdentity, subject)
        is_new = False
        if link_user_id is not None:
            user = db.get(User, link_user_id)
            if not user or not user.is_active or revoked(user, started_at):
                return finish(error='expired')
            existing = db.query(YandexIdentity).filter_by(user_id=user.id).first()
            if (identity and identity.user_id != user.id) or (existing and existing.subject != subject):
                return finish(error='linked_elsewhere')
            if not identity:
                db.add(YandexIdentity(subject=subject, user_id=user.id))
        elif identity:
            user = db.get(User, identity.user_id)
            if not user or not user.is_active:
                return finish(error='inactive')
        else:
            if not isinstance(email, str) or len(email) > 255 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                return finish(error='profile')
            email = email.strip().lower()
            if db.query(User).filter(func.lower(User.email) == email).first():
                return finish(error='existing_account')
            username = 'yandex_' + secrets.token_hex(12)
            name = info.get('real_name') or info.get('display_name')
            user = User(email=email, username=username, full_name=name[:255] if isinstance(name, str) else None,
                        hashed_password=None, is_active=True, email_verified=True)
            db.add(user)
            db.flush()
            db.add(YandexIdentity(subject=subject, user_id=user.id))
            is_new = True
        ticket = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        db.add(YandexTicket(ticket_hash=digest(ticket), frontend_challenge=frontend_challenge,
                            user_id=user.id, is_new=is_new, issued_at=now,
                            expires_at=now + timedelta(seconds=90)))
        db.commit()
        return finish(ticket=ticket)
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        db.rollback()
        return finish(error='provider')
    except IntegrityError:
        db.rollback()
        return finish(error='existing_account')


@router.post('/exchange')
@limiter.limit('10/minute')
def exchange(request: Request, payload: ExchangeRequest, db: Session = Depends(get_db)):
    ticket = db.get(YandexTicket, digest(payload.code))
    if not ticket or ticket.expires_at < datetime.utcnow() or not secrets.compare_digest(ticket.frontend_challenge, challenge(payload.verifier)):
        raise HTTPException(400, 'Invalid or expired sign-in')
    user = db.get(User, ticket.user_id)
    if not user or not user.is_active or revoked(user, ticket.issued_at):
        raise HTTPException(400, 'Invalid or expired sign-in')
    is_new = ticket.is_new
    count = db.query(YandexTicket).filter_by(ticket_hash=ticket.ticket_hash).delete()
    db.commit()
    if count != 1:
        raise HTTPException(400, 'Invalid or expired sign-in')
    return JSONResponse({'access_token': create_access_token({'sub': str(user.id)}), 'new_user': is_new},
                        headers={'Cache-Control': 'no-store'})
