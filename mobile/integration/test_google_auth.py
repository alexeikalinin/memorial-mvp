"""Real Google handoff endpoints, synthetic provider: no external Google account is used."""
import base64
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

import pytest

VERIFIER='x'*64
CHALLENGE=base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip('=')


@pytest.fixture
def google(monkeypatch):
    from app.config import settings
    import app.api.mobile_auth as mobile
    monkeypatch.setattr(settings,'GOOGLE_CLIENT_ID','synthetic-google-client')
    monkeypatch.setattr(settings,'GOOGLE_CLIENT_SECRET','synthetic-google-secret')
    monkeypatch.setattr(settings,'PUBLIC_API_URL','https://api.example')
    profile={'sub':'google-user-123','email':'test@example.com','email_verified':True,'name':'Test User'}
    calls=[]
    class Provider:
        def __init__(self,*args,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def post(self,url,data):
            calls.append(data)
            return type('Reply',(),{'status_code':200,'json':lambda self:{'access_token':'google-access-only-on-server'}})()
        async def get(self,url,headers):
            return type('Reply',(),{'status_code':200,'json':lambda self:profile})()
    monkeypatch.setattr(mobile.httpx,'AsyncClient',Provider)
    return profile,calls


def begin(client):
    response=client.post('/api/v1/auth/mobile/google/start',json={'challenge':CHALLENGE})
    assert response.status_code==200,response.text
    data=response.json()
    query=parse_qs(urlparse(data['authorization_url']).query)
    assert query['redirect_uri']==['https://api.example/api/v1/auth/google/callback']
    return data['attempt_id'],query['state'][0]


def finish(client,state):
    response=client.get('/api/v1/auth/google/callback',params={'state':state,'code':'synthetic-provider-code'},follow_redirects=False)
    assert response.status_code==302,response.text
    location=response.headers['location']
    assert location.startswith('vspomin://oauth/callback?')
    assert 'access_token' not in location and 'token=' not in location
    return parse_qs(urlparse(location).query)


def test_google_mobile_reuses_web_account_and_existing_memorials(client,registered_user,auth_headers,google):
    page=client.post('/api/v1/memorials/',json={'name':'Существующая страница'},headers=auth_headers).json()
    attempt,state=begin(client)
    callback=finish(client,state)
    assert callback['attempt']==[attempt]
    response=client.post('/api/v1/auth/mobile/google/exchange',json={'attempt_id':attempt,'verifier':VERIFIER,'code':callback['code'][0]})
    assert response.status_code==200,response.text
    assert response.headers['cache-control']=='no-store'
    assert response.json()['user']['id']==registered_user['id']
    headers={'Authorization':'Bearer '+response.json()['access_token']}
    assert client.get(f"/api/v1/memorials/{page['id']}",headers=headers).json()['current_user_role']=='owner'
    assert google[1][0]['redirect_uri']=='https://api.example/api/v1/auth/google/callback'
    assert 'client_secret' in google[1][0]


@pytest.mark.parametrize('wrong',['verifier','code'])
def test_intercepted_callback_or_attempt_cannot_be_redeemed_without_both_proofs(client,registered_user,google,wrong):
    attempt,state=begin(client);callback=finish(client,state)
    payload={'attempt_id':attempt,'verifier':VERIFIER,'code':callback['code'][0]}
    payload[wrong]='z'*(64 if wrong=='verifier' else 43)
    assert client.post('/api/v1/auth/mobile/google/exchange',json=payload).status_code==400
    payload.update(verifier=VERIFIER,code=callback['code'][0])
    assert client.post('/api/v1/auth/mobile/google/exchange',json=payload).status_code==200
    assert client.post('/api/v1/auth/mobile/google/exchange',json=payload).status_code==400


def test_expired_attempt_and_tampered_state_fail(client,db_session,registered_user,google):
    from app.mobile_auth_models import MobileGoogleAttempt
    attempt,state=begin(client)
    invalid=client.get('/api/v1/auth/google/callback',params={'state':state+'broken','code':'test'},follow_redirects=False)
    assert invalid.status_code==400
    row=db_session.get(MobileGoogleAttempt,attempt);row.expires_at=datetime.utcnow()-timedelta(seconds=1);db_session.commit()
    assert client.get('/api/v1/auth/google/callback',params={'state':state,'code':'test'},follow_redirects=False).status_code==400


def test_callback_is_consumed_once(client,registered_user,google):
    _,state=begin(client);finish(client,state)
    assert client.get('/api/v1/auth/google/callback',params={'state':state,'code':'test'},follow_redirects=False).status_code==400


@pytest.mark.parametrize('case',['unverified','disabled','conflict','missing_email'])
def test_google_cannot_attach_unverified_conflicting_or_disabled_identity(client,registered_user,db_session,google,case):
    from app.models import User
    user=db_session.get(User,registered_user['id'])
    if case=='unverified':google[0]['email_verified']=False
    elif case=='disabled':user.is_active=False;db_session.commit()
    elif case=='conflict':user.google_id='different-google-sub';db_session.commit()
    else:google[0].pop('email')
    attempt,state=begin(client);callback=finish(client,state)
    assert callback.get('error')==['google_sign_in_failed']
    assert client.post('/api/v1/auth/mobile/google/exchange',json={'attempt_id':attempt,'verifier':VERIFIER,'code':'z'*43}).status_code==400


def test_cancelled_google_flow_returns_to_app_without_session(client,registered_user,google):
    attempt,state=begin(client)
    response=client.get('/api/v1/auth/google/callback',params={'state':state,'error':'access_denied'},follow_redirects=False)
    assert response.status_code==302
    assert 'error=google_sign_in_failed' in response.headers['location']
    assert client.post('/api/v1/auth/mobile/google/exchange',json={'attempt_id':attempt,'verifier':VERIFIER,'code':'z'*43}).status_code==400


def test_existing_web_google_flow_is_unchanged(client,registered_user,google,monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings,'FRONTEND_URL','https://vspomin.ai/app')
    start=client.get('/api/v1/auth/google',follow_redirects=False)
    assert start.status_code==307
    response=client.get('/api/v1/auth/google/callback',params={'code':'synthetic-web-code'},follow_redirects=False)
    assert response.status_code==302
    assert response.headers['location'].startswith('https://vspomin.ai/app/auth/callback?token=')


def test_new_google_user_is_created_once(client,google):
    attempt,state=begin(client);callback=finish(client,state)
    response=client.post('/api/v1/auth/mobile/google/exchange',json={'attempt_id':attempt,'verifier':VERIFIER,'code':callback['code'][0]})
    assert response.status_code==200
    assert response.json()['user']['email_verified'] is True


def test_start_rejects_unconfigured_google_and_invalid_challenge(client,monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings,'GOOGLE_CLIENT_ID','')
    assert client.post('/api/v1/auth/mobile/google/start',json={'challenge':CHALLENGE}).status_code==501
    assert client.post('/api/v1/auth/mobile/google/start',json={'challenge':'bad'}).status_code==422
