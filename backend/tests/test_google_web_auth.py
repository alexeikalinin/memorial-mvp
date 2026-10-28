"""Google and Yandex must reach one account only after explicit authenticated linking."""
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import httpx
import pytest
from app.api import google_web_auth as api
from app.models import User
from app.google_web_auth_models import GoogleWebAttempt, GoogleWebTicket
from app.yandex_auth_models import YandexIdentity


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(api.settings, 'GOOGLE_CLIENT_ID', 'test-client')
    monkeypatch.setattr(api.settings, 'GOOGLE_CLIENT_SECRET', 'test-secret')
    monkeypatch.setattr(api.settings, 'PUBLIC_API_URL', 'http://testserver')
    monkeypatch.setattr(api.settings, 'FRONTEND_URL', 'http://frontend/app')
    monkeypatch.setattr(api.settings, 'DEBUG', False)


def start(client, link=False, headers=None):
    verifier = 'v' * 43
    response = client.post('/api/v1/auth/google/start', json={'challenge':api.challenge(verifier), 'link':link}, headers=headers or {})
    assert response.status_code == 200
    qs = parse_qs(urlparse(response.json()['url']).query)
    assert qs['code_challenge_method'] == ['S256']
    assert qs['redirect_uri'] == ['http://testserver/api/v1/auth/google/callback']
    return qs['state'][0], verifier


def provider(monkeypatch, **overrides):
    info = {'sub':'google-123', 'email':'new-google@example.com', 'email_verified':True, 'name':'Google User'}
    info.update(overrides)
    calls = []
    class Client:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,data):
            assert url == 'https://oauth2.googleapis.com/token'
            assert data['code_verifier'] and data['client_secret'] == 'test-secret'
            calls.append(data)
            return httpx.Response(200,json={'access_token':'private-google-token'})
        async def get(self,url,**kwargs):
            assert url == 'https://www.googleapis.com/oauth2/v3/userinfo'
            return httpx.Response(200,json=info)
    monkeypatch.setattr(api.httpx,'AsyncClient',Client)
    return calls


def complete(client,state):
    return client.get('/api/v1/auth/google/callback',params={'state':state,'code':'provider-code'},follow_redirects=False)


def exchange(client,response,verifier):
    data = parse_qs(urlparse(response.headers['location']).fragment)
    return client.post('/api/v1/auth/google/exchange',json={'code':data['google_code'][0],'verifier':verifier})


def test_new_and_returning_google_user(client,db_session,monkeypatch):
    provider(monkeypatch)
    state, verifier = start(client)
    response = complete(client,state)
    assert 'token=' not in response.headers['location']
    result = exchange(client,response,verifier)
    assert result.status_code == 200 and result.json()['new_user'] is True
    assert exchange(client,response,verifier).status_code == 400
    uid = db_session.query(User).one().id
    state, verifier = start(client)
    result = exchange(client,complete(client,state),verifier)
    assert result.status_code == 200 and result.json()['new_user'] is False
    me = client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+result.json()['access_token']})
    assert me.json()['id'] == uid and me.json()['email_verified'] is True
    assert db_session.query(User).count() == 1


def test_yandex_user_explicitly_connects_different_google_email(client,registered_user,auth_headers,memorial,db_session,monkeypatch):
    db_session.add(YandexIdentity(subject='existing-yandex',user_id=registered_user['id']))
    db_session.commit()
    provider(monkeypatch,email='different-google@example.com')
    state, verifier = start(client,link=True,headers=auth_headers)
    result = exchange(client,complete(client,state),verifier)
    assert result.status_code == 200 and result.json()['new_user'] is False
    user = db_session.get(User,registered_user['id'])
    assert user.google_id == 'google-123' and user.email == 'test@example.com'
    assert db_session.query(User).count() == 1
    state, verifier = start(client)
    result = exchange(client,complete(client,state),verifier)
    headers = {'Authorization':'Bearer '+result.json()['access_token']}
    assert client.get('/api/v1/auth/me',headers=headers).json()['id'] == user.id
    assert client.get(f'/api/v1/memorials/{memorial["id"]}',headers=headers).status_code == 200
    assert client.get('/api/v1/auth/google/connection',headers=headers).json() == {'connected':True}
    assert client.get('/api/v1/auth/yandex/connection',headers=headers).json() == {'connected':True}


def test_same_email_never_auto_links(client,registered_user,db_session,monkeypatch):
    provider(monkeypatch,email='TEST@example.com')
    state,_ = start(client)
    assert 'existing_account' in complete(client,state).headers['location']
    assert db_session.get(User,registered_user['id']).google_id is None
    assert db_session.query(User).count() == 1
    assert client.post('/api/v1/auth/google/start',json={'challenge':'a'*43,'link':True}).status_code == 401
    assert client.get('/api/v1/auth/google/connection').status_code == 401


def test_cannot_take_or_replace_google_connection(client,registered_user,auth_headers,second_user_headers,db_session,monkeypatch):
    provider(monkeypatch)
    state,verifier = start(client,True,auth_headers)
    assert exchange(client,complete(client,state),verifier).status_code == 200
    state,_ = start(client,True,second_user_headers)
    assert 'linked_elsewhere' in complete(client,state).headers['location']
    provider(monkeypatch,sub='different-subject')
    state,_ = start(client,True,auth_headers)
    assert 'linked_elsewhere' in complete(client,state).headers['location']
    assert db_session.get(User,registered_user['id']).google_id == 'google-123'


def test_state_cookie_and_replay(client,monkeypatch):
    calls = provider(monkeypatch)
    state,_ = start(client)
    cookie = client.cookies.get(api.COOKIE)
    client.cookies.clear()
    assert 'expired' in complete(client,state).headers['location'] and not calls
    client.cookies.set(api.COOKIE,cookie)
    assert 'google_code' in complete(client,state).headers['location']
    assert 'expired' in complete(client,state).headers['location']
    assert len(calls) == 1


@pytest.mark.parametrize('overrides',[{'sub':None},{'email':None},{'email_verified':False},{'email_verified':'true'}])
def test_invalid_profile_rejected(client,db_session,monkeypatch,overrides):
    provider(monkeypatch,**overrides)
    state,_=start(client)
    assert 'profile' in complete(client,state).headers['location']
    assert db_session.query(User).count() == 0


def test_expiry_wrong_tab_and_reset(client,registered_user,auth_headers,db_session,monkeypatch):
    provider(monkeypatch)
    state,verifier=start(client,True,auth_headers)
    response=complete(client,state)
    assert exchange(client,response,'x'*43).status_code == 400
    db_session.query(GoogleWebTicket).update({'expires_at':datetime.utcnow()-timedelta(seconds=1)})
    db_session.commit()
    assert exchange(client,response,verifier).status_code == 400
    state,_=start(client,True,auth_headers)
    user=db_session.get(User,registered_user['id']);user.tokens_invalid_before=datetime.utcnow()+timedelta(seconds=1)
    db_session.commit()
    assert 'expired' in complete(client,state).headers['location']


def test_legacy_url_starts_bound_browser_flow(client,monkeypatch):
    calls=provider(monkeypatch)
    assert client.get('/api/v1/auth/google',follow_redirects=False).headers['location'] == 'http://frontend/app/auth/google/start'
    assert 'expired' in complete(client,'missing-state').headers['location']
    assert not calls


def test_mobile_does_not_bypass_explicit_linking(client,registered_user,db_session):
    from app.api.mobile_auth import _google_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        _google_user(db_session,{'sub':'new-mobile-google','email':'TEST@example.com','email_verified':True})
    assert exc.value.status_code == 409
    assert db_session.get(User,registered_user['id']).google_id is None


def test_archive_has_no_google_transactions(auth_client,db_session):
    from zipfile import ZipFile
    import io,json
    state,_=start(auth_client,True)
    assert db_session.query(GoogleWebAttempt).count() == 1
    response=auth_client.get('/api/v1/account/export')
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as z:
        data=json.loads(z.read('data.json'))
        assert 'google_web_attempts' not in data and 'google_web_tickets' not in data


def test_google_user_connects_yandex_and_returns_to_same_account(client, registered_user, auth_headers, memorial, db_session, monkeypatch):
    from app.api import yandex_auth as ya
    monkeypatch.setattr(ya.settings, 'YANDEX_CLIENT_ID', 'yandex-test')
    monkeypatch.setattr(ya.settings, 'YANDEX_CLIENT_SECRET', 'yandex-secret')
    user = db_session.get(User, registered_user['id'])
    user.google_id = 'existing-google'
    db_session.commit()
    class Provider:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, *args, **kwargs): return httpx.Response(200, json={'access_token': 'private'})
        async def get(self, *args, **kwargs): return httpx.Response(200, json={'id':'new-yandex', 'client_id':'yandex-test', 'default_email':'other@yandex.ru', 'display_name':'Person'})
    monkeypatch.setattr(ya.httpx, 'AsyncClient', Provider)
    for link in (True, False):
        verifier = 'y' * 43
        response = client.post('/api/v1/auth/yandex/start', json={'challenge':ya.challenge(verifier), 'link':link}, headers=auth_headers if link else {})
        state = parse_qs(urlparse(response.json()['url']).query)['state'][0]
        callback = client.get('/api/v1/auth/yandex/callback', params={'code':'code', 'state':state}, follow_redirects=False)
        code = parse_qs(urlparse(callback.headers['location']).fragment)['yandex_code'][0]
        result = client.post('/api/v1/auth/yandex/exchange', json={'code':code, 'verifier':verifier})
        assert result.status_code == 200
        headers = {'Authorization':'Bearer '+result.json()['access_token']}
        assert client.get('/api/v1/auth/me', headers=headers).json()['id'] == user.id
        assert client.get(f'/api/v1/memorials/{memorial["id"]}', headers=headers).status_code == 200
    assert db_session.query(User).count() == 1
    assert user.google_id == 'existing-google' and user.email == 'test@example.com'


def test_google_cancellation_does_not_contact_provider(client, monkeypatch):
    calls = provider(monkeypatch)
    state, _ = start(client)
    response = client.get('/api/v1/auth/google/callback', params={'state':state, 'error':'access_denied'}, follow_redirects=False)
    assert 'cancelled' in response.headers['location'] and not calls
