"""Security and account continuity for Yandex web sign-in; no real provider calls."""
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import httpx
import pytest
from app.api import yandex_auth as api
from app.models import User
from app.yandex_auth_models import YandexIdentity, YandexAttempt, YandexTicket


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(api.settings, 'YANDEX_CLIENT_ID', 'test-client')
    monkeypatch.setattr(api.settings, 'YANDEX_CLIENT_SECRET', 'test-secret')
    monkeypatch.setattr(api.settings, 'PUBLIC_API_URL', 'http://testserver')
    monkeypatch.setattr(api.settings, 'FRONTEND_URL', 'http://frontend/app')
    monkeypatch.setattr(api.settings, 'DEBUG', False)


def start(client, link=False, headers=None):
    verifier = 'v' * 43
    r = client.post('/api/v1/auth/yandex/start', json={'challenge': api.challenge(verifier), 'link': link}, headers=headers or {})
    assert r.status_code == 200
    qs = parse_qs(urlparse(r.json()['url']).query)
    assert qs['code_challenge_method'] == ['S256']
    return qs['state'][0], verifier


def provider(monkeypatch, **override):
    info = {'id': 'yandex-123', 'client_id': 'test-client', 'default_email': 'yandex@example.com', 'real_name': 'Yandex User'}
    info.update(override)
    calls = []
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, data):
            calls.append(data)
            return httpx.Response(200, json={'access_token': 'private-provider-token'})
        async def get(self, url, **kwargs):
            return httpx.Response(200, json=info)
    monkeypatch.setattr(api.httpx, 'AsyncClient', Client)
    return calls


def complete(client, state):
    return client.get('/api/v1/auth/yandex/callback', params={'code': 'provider-code', 'state': state}, follow_redirects=False)


def exchange(client, response, verifier):
    fragment = parse_qs(urlparse(response.headers['location']).fragment)
    return client.post('/api/v1/auth/yandex/exchange', json={'code': fragment['yandex_code'][0], 'verifier': verifier})


def test_registration_repeat_and_single_use(client, db_session, monkeypatch):
    calls = provider(monkeypatch)
    state, verifier = start(client)
    response = complete(client, state)
    assert 'token=' not in response.headers['location']
    assert db_session.query(YandexAttempt).count() == 0
    first = exchange(client, response, verifier)
    assert first.status_code == 200 and first.json()['new_user'] is True
    assert exchange(client, response, verifier).status_code == 400
    me = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer ' + first.json()['access_token']})
    uid = me.json()['id']
    assert me.json()['email_verified'] is True
    assert calls[0]['code_verifier']
    state, verifier = start(client)
    again = exchange(client, complete(client, state), verifier)
    assert again.status_code == 200 and again.json()['new_user'] is False
    assert db_session.query(User).count() == 1
    assert db_session.query(YandexIdentity).one().user_id == uid


def test_state_cookie_and_replay(client, monkeypatch):
    calls = provider(monkeypatch)
    state, _ = start(client)
    cookie = client.cookies.get(api.COOKIE)
    client.cookies.clear()
    assert 'expired' in complete(client, state).headers['location']
    assert not calls
    client.cookies.set(api.COOKIE, cookie)
    assert 'yandex_code' in complete(client, state).headers['location']
    assert 'expired' in complete(client, state).headers['location']
    assert len(calls) == 1


def test_email_collision_then_explicit_link(client, registered_user, auth_headers, db_session, monkeypatch):
    provider(monkeypatch, default_email='TEST@example.com')
    state, _ = start(client)
    assert 'existing_account' in complete(client, state).headers['location']
    assert db_session.query(YandexIdentity).count() == 0
    assert client.post('/api/v1/auth/yandex/start', json={'challenge': 'a'*43, 'link': True}).status_code == 401
    state, verifier = start(client, link=True, headers=auth_headers)
    result = exchange(client, complete(client, state), verifier)
    assert result.status_code == 200
    assert db_session.query(YandexIdentity).one().user_id == registered_user['id']
    assert db_session.query(User).count() == 1


@pytest.mark.parametrize('override', [{'id': None}, {'default_email': None}, {'client_id': 'wrong'}, {'default_email': 'bad'}])
def test_missing_profile_rejected(client, db_session, monkeypatch, override):
    provider(monkeypatch, **override)
    state, _ = start(client)
    assert 'profile' in complete(client, state).headers['location']
    assert db_session.query(YandexIdentity).count() == 0


def test_frontend_verifier_and_expiry(client, db_session, monkeypatch):
    provider(monkeypatch)
    state, verifier = start(client)
    response = complete(client, state)
    assert exchange(client, response, 'x'*43).status_code == 400
    ticket = db_session.query(YandexTicket).one()
    ticket.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()
    assert exchange(client, response, verifier).status_code == 400


def test_expired_state_and_cancel(client, db_session, monkeypatch):
    calls = provider(monkeypatch)
    state, _ = start(client)
    attempt = db_session.query(YandexAttempt).one()
    attempt.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()
    assert 'expired' in complete(client, state).headers['location']
    state, _ = start(client)
    response = client.get('/api/v1/auth/yandex/callback', params={'state':state, 'error':'access_denied'}, follow_redirects=False)
    assert 'cancelled' in response.headers['location'] and not calls


def test_disabled_user_cannot_return(client, db_session, monkeypatch):
    provider(monkeypatch)
    state, verifier = start(client)
    response = complete(client, state)
    db_session.query(User).update({'is_active':False})
    db_session.commit()
    assert exchange(client, response, verifier).status_code == 400
    state, _ = start(client)
    assert 'inactive' in complete(client, state).headers['location']


def test_config_and_secure_cookie(client, monkeypatch):
    monkeypatch.setattr(api.settings, 'PUBLIC_API_URL', 'https://api.example.com')
    response = client.post('/api/v1/auth/yandex/start', json={'challenge':'a'*43})
    cookie = response.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=lax' in cookie
    monkeypatch.setattr(api.settings, 'YANDEX_CLIENT_SECRET', '')
    assert client.get('/api/v1/auth/yandex/status').json() == {'enabled':False}
    assert client.post('/api/v1/auth/yandex/start', json={'challenge':'a'*43}).status_code == 503


def test_cannot_move_identity_between_users(client, auth_headers, second_user_headers, db_session, monkeypatch):
    provider(monkeypatch)
    state, verifier = start(client, link=True, headers=auth_headers)
    assert exchange(client, complete(client, state), verifier).status_code == 200
    linked = db_session.query(YandexIdentity).one().user_id
    state, _ = start(client, link=True, headers=second_user_headers)
    assert 'linked_elsewhere' in complete(client, state).headers['location']
    assert db_session.query(YandexIdentity).one().user_id == linked


def test_reset_invalidates_pending_link(client, auth_headers, db_session, monkeypatch):
    provider(monkeypatch)
    state, _ = start(client, link=True, headers=auth_headers)
    user = db_session.query(User).filter_by(email='test@example.com').one()
    user.tokens_invalid_before = datetime.utcnow() + timedelta(seconds=1)
    db_session.commit()
    assert 'expired' in complete(client, state).headers['location']
    assert db_session.query(YandexIdentity).count() == 0


def test_provider_failure_is_safe(client, db_session, monkeypatch):
    class Failed:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, *args, **kwargs): raise httpx.ConnectError('unavailable')
    monkeypatch.setattr(api.httpx, 'AsyncClient', Failed)
    state, _ = start(client)
    response = complete(client, state)
    assert 'yandex_error=provider' in response.headers['location']
    assert db_session.query(YandexAttempt).count() == 0
    assert db_session.query(YandexIdentity).count() == 0
