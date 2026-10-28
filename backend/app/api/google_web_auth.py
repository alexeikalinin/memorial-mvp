"""Authorization-code + PKCE login. Never returns provider tokens to the browser."""
import re
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import _get_user_from_token, create_access_token
from app.config import settings
from app.db import get_db
from app.limiter import limiter
from app.models import User
from app.google_web_auth_models import GoogleWebAttempt, GoogleWebTicket
from app.api.yandex_auth import StartRequest, ExchangeRequest, digest, challenge, revoked

router = APIRouter(prefix='/auth/google', tags=['auth'])
COOKIE = 'google_browser'
COOKIE_PATH = settings.API_V1_PREFIX + '/auth/google'


def frontend():
    return settings.FRONTEND_URL.rstrip('/')


def callback_uri():
    return (settings.PUBLIC_API_URL or 'http://localhost:8000').rstrip('/') + COOKIE_PATH + '/callback'


def configured():
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def finish(error=None, ticket=None):
    params = {'google_error': error} if error else {'google_code': ticket}
    response = RedirectResponse(frontend() + '/auth/google/callback#' + urlencode(params), status_code=302)
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@router.get('/status')
def status():
    return {'enabled': configured()}


@router.get('/connection')
def connection(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get('authorization', '').removeprefix('Bearer ')
    user = _get_user_from_token(token, db)
    if not user:
        raise HTTPException(401, 'Authentication required')
    return {'connected': bool(user.google_id)}


@router.post('/start')
@limiter.limit('10/minute')
def start(request: Request, payload: StartRequest, db: Session = Depends(get_db)):
    if not configured():
        raise HTTPException(503, 'Google sign-in is not configured')
    user = None
    if payload.link:
        token = request.headers.get('authorization', '').removeprefix('Bearer ')
        user = _get_user_from_token(token, db)
        if not user:
            raise HTTPException(401, 'Authentication required')
    now = datetime.utcnow()
    db.query(GoogleWebAttempt).filter(GoogleWebAttempt.expires_at < now).delete()
    db.query(GoogleWebTicket).filter(GoogleWebTicket.expires_at < now).delete()
    state, browser, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    db.add(GoogleWebAttempt(state_hash=digest(state), browser_hash=digest(browser),
                         provider_verifier=verifier, frontend_challenge=payload.challenge,
                         user_id=user.id if user else None, started_at=now,
                         expires_at=now + timedelta(minutes=10)))
    db.commit()
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
        'response_type': 'code', 'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': callback_uri(), 'scope': 'openid email profile',
        'state': state, 'code_challenge': challenge(verifier),
        'code_challenge_method': 'S256', 'prompt': 'select_account',
    })
    response = JSONResponse({'url': url}, headers={'Cache-Control': 'no-store'})
    response.set_cookie(COOKIE, browser, max_age=600, path=COOKIE_PATH,
                        httponly=True, secure=callback_uri().startswith('https://'), samesite='lax')
    return response


async def complete(request: Request, code: str | None = None, state: str | None = None,
                   error: str | None = None, db: Session = Depends(get_db)):
    if not configured():
        return finish(error='unavailable')
    attempt = db.get(GoogleWebAttempt, digest(state or ''))
    browser = request.cookies.get(COOKIE, '')
    if not attempt or attempt.expires_at < datetime.utcnow() or not browser or not secrets.compare_digest(attempt.browser_hash, digest(browser)):
        return finish(error='expired')
    # Atomic consumption before making a provider request, including cancellation.
    values = (attempt.provider_verifier, attempt.frontend_challenge, attempt.user_id, attempt.started_at)
    count = db.query(GoogleWebAttempt).filter_by(state_hash=attempt.state_hash).delete()
    db.commit()
    if count != 1:
        return finish(error='expired')
    verifier, frontend_challenge, link_user_id, started_at = values
    if error or not code:
        return finish(error='cancelled')
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post('https://oauth2.googleapis.com/token', data={
                'grant_type': 'authorization_code', 'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID, 'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'code_verifier': verifier, 'redirect_uri': callback_uri(),
            })
            if token_response.status_code != 200:
                return finish(error='provider')
            access_token = token_response.json().get('access_token')
            if not isinstance(access_token, str) or not access_token:
                return finish(error='provider')
            profile = await client.get('https://www.googleapis.com/oauth2/v3/userinfo',
                                       headers={'Authorization': 'Bearer ' + access_token})
            if profile.status_code != 200:
                return finish(error='provider')
            info = profile.json()
        subject, email = info.get('sub'), info.get('email')
        if not isinstance(subject, str) or not subject or len(subject) > 255:
            return finish(error='profile')
        if info.get('email_verified') is not True:
            return finish(error='profile')
        identity_user = db.query(User).filter(User.google_id == subject).first()
        is_new = False
        if link_user_id is not None:
            user = db.query(User).filter(User.id == link_user_id).with_for_update().first()
            if not user or not user.is_active or revoked(user, started_at):
                return finish(error='expired')
            if (identity_user and identity_user.id != user.id) or (user.google_id and user.google_id != subject):
                return finish(error='linked_elsewhere')
            user.google_id = subject
        elif identity_user:
            user = identity_user
            if not user.is_active:
                return finish(error='inactive')
        else:
            if not isinstance(email, str) or len(email) > 255 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                return finish(error='profile')
            email = email.strip().lower()
            if db.query(User).filter(func.lower(User.email) == email).first():
                return finish(error='existing_account')
            username = 'google_' + secrets.token_hex(12)
            name = info.get('name')
            user = User(email=email, username=username, full_name=name[:255] if isinstance(name, str) else None,
                        hashed_password=None, google_id=subject, is_active=True, email_verified=True)
            db.add(user)
            db.flush()
            is_new = True
        ticket = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        db.add(GoogleWebTicket(ticket_hash=digest(ticket), frontend_challenge=frontend_challenge,
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
    ticket = db.get(GoogleWebTicket, digest(payload.code))
    if not ticket or ticket.expires_at < datetime.utcnow() or not secrets.compare_digest(ticket.frontend_challenge, challenge(payload.verifier)):
        raise HTTPException(400, 'Invalid or expired sign-in')
    user = db.get(User, ticket.user_id)
    if not user or not user.is_active or revoked(user, ticket.issued_at):
        raise HTTPException(400, 'Invalid or expired sign-in')
    is_new = ticket.is_new
    count = db.query(GoogleWebTicket).filter_by(ticket_hash=ticket.ticket_hash).delete()
    db.commit()
    if count != 1:
        raise HTTPException(400, 'Invalid or expired sign-in')
    return JSONResponse({'access_token': create_access_token({'sub': str(user.id)}), 'new_user': is_new},
                        headers={'Cache-Control': 'no-store'})
