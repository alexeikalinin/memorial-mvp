from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.models import MemorialSign


def public_memorial(auth_client):
    return auth_client.post('/api/v1/memorials/', json={'name': 'Signs demo', 'is_public': True}).json()['id']


def test_multiple_visitors_and_expiry(auth_client, client, db_session, monkeypatch):
    monkeypatch.setattr('app.auth._get_dev_user', lambda db: None)
    memorial_id = public_memorial(auth_client)
    path = f'/api/v1/memorials/{memorial_id}/signs'
    first_headers = {'Authorization': '', 'X-Memorial-Visitor': str(uuid4())}
    first = client.post(path, headers=first_headers, json={'kind': 'candle', 'variant': 'classic', 'display_name': 'Анна'})
    assert first.status_code == 200
    assert datetime.fromisoformat(first.json()['expires_at']) - datetime.fromisoformat(first.json()['created_at']) == timedelta(hours=24)
    assert datetime.fromisoformat(first.json()['expires_at']).tzinfo is not None
    repeated = client.post(path, headers=first_headers, json={'kind': 'candle', 'variant': 'lantern'})
    assert repeated.json()['id'] == first.json()['id']
    assert repeated.json()['expires_at'] == first.json()['expires_at']
    second = client.post(path, headers={'Authorization': '', 'X-Memorial-Visitor': str(uuid4())}, json={'kind': 'candle', 'variant': 'lampada'})
    assert second.json()['id'] != first.json()['id']
    flower = client.post(path, headers=first_headers, json={'kind': 'flowers', 'variant': 'red_carnations'})
    assert flower.status_code == 200
    assert client.get(path, headers={'Authorization': ''}).json()['candle_lit']
    db_session.query(MemorialSign).filter(MemorialSign.id == first.json()['id']).update({'expires_at': datetime.now(timezone.utc)-timedelta(seconds=1)})
    db_session.commit()
    assert client.get(path, headers={'Authorization': ''}).json()['candle_lit']
    db_session.query(MemorialSign).update({'expires_at': datetime.now(timezone.utc)-timedelta(seconds=1)})
    db_session.commit()
    assert client.get(path, headers={'Authorization': ''}).json() == {'items': [], 'candle_lit': False}
    journal = auth_client.get(path + '/journal').json()
    assert journal['total'] == 3
    assert len(journal['items']) == 3
    assert 'visitor_key' not in journal['items'][0]


def test_sign_privacy_and_validation(auth_client, client, second_user_headers, memorial, monkeypatch):
    monkeypatch.setattr('app.auth._get_dev_user', lambda db: None)
    path = f"/api/v1/memorials/{memorial['id']}/signs"
    assert client.get(path, headers={'Authorization': ''}).status_code in (401, 403, 404)
    assert client.get(path+'/journal', headers=second_user_headers).status_code in (403, 404)
    assert client.post(path, headers={'Authorization': '', 'X-Memorial-Visitor': str(uuid4())}, json={'kind':'flowers','variant':'red_carnations'}).status_code in (401,403,404)
    assert auth_client.post(path, json={'kind':'flowers','variant':'classic'}).status_code == 422
    assert auth_client.post(path, json={'kind':'candle','variant':'classic','display_name':'x'*81}).status_code == 422


def test_appearance_layout_validation(auth_client, memorial):
    path = f"/api/v1/memorials/{memorial['id']}"
    valid = {'quote': 'Text', 'font': 'sans', 'font_size': 32, 'layout': {'flowers': {'x': .8, 'y': .6, 'scale': 1.5}}}
    res = auth_client.patch(path, json={'appearance_settings': valid})
    assert res.status_code == 200
    assert res.json()['appearance_settings']['layout'] == {'flowers': {'x':.8, 'y':.6, 'scale':1.5}, 'quote':None, 'candle':None}
    for bad in [{'font_size':49}, {'layout':{'flowers':{'x':2,'y':0}}}, {'layout':{'candle':{'x':.1,'y':.1,'scale':3}}}]:
        assert auth_client.patch(path, json={'appearance_settings':bad}).status_code == 422
