"""Owner consent, graph privacy, invalid generations, and ownership handover."""
import pytest
from app.config import settings
from app.models import User, MemorialAccess, UserRole, Memorial, FamilyRelationship


@pytest.fixture(autouse=True)
def no_demo_auth(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "INVESTOR_DEMO_MODE", False)
    monkeypatch.setattr(settings, "GLOBAL_ADMIN_EMAILS", "")


def make(client, headers, name, public=True):
    r = client.post('/api/v1/memorials/', headers=headers, json={'name': name, 'is_public': public})
    assert r.status_code == 201, r.text
    return r.json()['id']


def link(client, headers, a, b, kind='sibling', public=False):
    return client.post(f'/api/v1/family/memorials/{a}/relationships', headers=headers,
                       json={'related_memorial_id': b, 'relationship_type': kind, 'is_public': public})


def test_cross_owner_consent_does_not_grant_edit(client, auth_headers, second_user_headers, db_session):
    a = make(client, auth_headers, 'Mother')
    b = make(client, second_user_headers, 'Uncle')
    r = link(client, auth_headers, a, b, public=True)
    assert r.status_code == 201 and r.json()['status'] == 'pending'
    request_id = r.json()['request_id']
    assert db_session.query(FamilyRelationship).count() == 0
    assert client.post(f'/api/v1/family/requests/{request_id}/respond', headers=auth_headers, json={'decision':'accept'}).status_code == 403
    inbox = client.get('/api/v1/family/requests', headers=second_user_headers).json()
    assert inbox[0]['can_respond'] is True
    assert client.post(f'/api/v1/family/requests/{request_id}/respond', headers=second_user_headers, json={'decision':'accept'}).status_code == 200
    assert db_session.query(FamilyRelationship).count() == 2
    nodes = client.get(f'/api/v1/family/memorials/{a}/full-tree', headers={'Authorization':''}).json()['nodes']
    assert {n['memorial_id'] for n in nodes} == {a, b}
    assert client.patch(f'/api/v1/memorials/{b}', headers=auth_headers, json={'description':'bad'}).status_code == 403
    assert client.post(f'/api/v1/family/requests/{request_id}/respond', headers=second_user_headers, json={'decision':'accept'}).status_code == 409


@pytest.mark.parametrize('endpoint',['full-tree','tree','relationships','hidden-connections','network-clusters'])
def test_no_private_page_or_private_bridge_leak(client, auth_headers, endpoint):
    a = make(client, auth_headers, 'Public origin')
    b = make(client, auth_headers, 'Private parent', False)
    c = make(client, auth_headers, 'Public beyond hidden parent')
    assert link(client, auth_headers, a, b, 'parent', True).status_code == 201
    assert link(client, auth_headers, b, c, 'parent', True).status_code == 201
    r = client.get(f'/api/v1/family/memorials/{a}/{endpoint}', headers={'Authorization':''})
    assert r.status_code == 200
    assert 'Private parent' not in r.text
    assert 'Public beyond hidden parent' not in r.text


def test_public_pages_do_not_publish_private_relation(client, auth_headers):
    a = make(client, auth_headers, 'Mother')
    b = make(client, auth_headers, 'Uncle')
    assert link(client, auth_headers, a, b).status_code == 201
    assert len(client.get(f'/api/v1/family/memorials/{a}/full-tree', headers={'Authorization':''}).json()['nodes']) == 1
    assert len(client.get(f'/api/v1/family/memorials/{a}/full-tree', headers=auth_headers).json()['nodes']) == 2


def test_search_filters_private_and_matches_name(client, auth_headers, second_user_headers):
    a = make(client, auth_headers, 'Nikolai Public')
    b = make(client, auth_headers, 'Nikolai Secret', False)
    result = client.get('/api/v1/family/search?q=Nikolai', headers=second_user_headers).json()
    assert [r['id'] for r in result] == [a]
    assert link(client, second_user_headers, a, b).status_code == 403


def test_cycles_conflicts_and_inverse_patch(client, auth_headers):
    a, b, c = [make(client, auth_headers, n) for n in ['A','B','C']]
    assert link(client, auth_headers, a, b, 'parent').status_code == 201
    assert link(client, auth_headers, b, c, 'parent').status_code == 201
    assert link(client, auth_headers, c, a, 'parent').status_code == 409
    assert link(client, auth_headers, a, b, 'child').status_code == 409
    rel = client.get(f'/api/v1/family/memorials/{a}/relationships', headers=auth_headers).json()[0]
    assert client.patch(f"/api/v1/family/relationships/{rel['id']}", headers=auth_headers, json={'relationship_type':'child'}).status_code == 400


def test_pending_duplicate_cancel_reject_and_resend(client, auth_headers, second_user_headers):
    a = make(client, auth_headers, 'A')
    b = make(client, second_user_headers, 'B')
    r = link(client, auth_headers, a, b).json()['request_id']
    assert link(client, auth_headers, a, b).status_code == 409
    assert client.delete(f'/api/v1/family/requests/{r}', headers=second_user_headers).status_code == 403
    assert client.delete(f'/api/v1/family/requests/{r}', headers=auth_headers).status_code == 204
    r = link(client, auth_headers, a, b).json()['request_id']
    assert client.post(f'/api/v1/family/requests/{r}/respond', headers=second_user_headers, json={'decision':'reject'}).status_code == 200
    assert link(client, auth_headers, a, b).status_code == 201


def test_ownership_transfer_recipient_must_accept_and_links_survive(client, auth_headers, second_user_headers, db_session):
    owner = db_session.query(User).filter_by(email='test@example.com').one()
    child = db_session.query(User).filter_by(email='other@example.com').one()
    child.email_verified = True
    db_session.commit()
    a = make(client, auth_headers, 'Father')
    b = make(client, auth_headers, 'Mother')
    link(client, auth_headers, a, b, 'spouse')
    r = client.post(f'/api/v1/memorials/{a}/ownership/transfer', headers=auth_headers,
                    json={'email':'other@example.com','keep_editor':True})
    assert r.status_code == 201, r.text
    tid = r.json()['id']
    assert db_session.get(Memorial, a).owner_id == owner.id
    assert client.post(f'/api/v1/memorials/ownership/transfers/{tid}/respond', headers=auth_headers, json={'decision':'accept'}).status_code == 403
    assert client.get('/api/v1/memorials/ownership/transfers', headers=second_user_headers).json()[0]['id'] == tid
    assert client.post(f'/api/v1/memorials/ownership/transfers/{tid}/respond', headers=second_user_headers, json={'decision':'accept'}).status_code == 200
    db_session.expire_all()
    assert db_session.get(Memorial, a).owner_id == child.id
    assert db_session.query(MemorialAccess).filter_by(memorial_id=a,user_id=child.id).one().role == UserRole.OWNER
    assert db_session.query(MemorialAccess).filter_by(memorial_id=a,user_id=owner.id).one().role == UserRole.EDITOR
    assert db_session.query(FamilyRelationship).count() == 2
    assert client.delete(f'/api/v1/memorials/{a}', headers=auth_headers).status_code == 403


def test_editor_access_request_does_not_transfer_ownership(client, auth_headers, second_user_headers, db_session):
    a = make(client, auth_headers, 'Father')
    before = db_session.get(Memorial, a).owner_id
    r = client.post(f'/api/v1/memorials/{a}/access/request', headers=second_user_headers,
                    json={'requested_role':'editor','message':'I am his daughter'})
    assert r.status_code == 201
    assert client.post(f"/api/v1/memorials/{a}/access/requests/{r.json()['id']}/approve", headers=auth_headers).status_code == 200
    assert db_session.get(Memorial, a).owner_id == before
    assert client.post(f'/api/v1/memorials/{a}/ownership/transfer', headers=second_user_headers,
                       json={'email':'test@example.com'}).status_code == 403


def test_family_memory_sync_requires_editor_and_limits_targets(client, auth_headers, second_user_headers, monkeypatch):
    a = make(client, auth_headers, 'Source')
    b = make(client, second_user_headers, 'Other owner')
    request_id = link(client, auth_headers, a, b).json()['request_id']
    assert client.post(f'/api/v1/family/requests/{request_id}/respond', headers=second_user_headers,
                       json={'decision': 'accept'}).status_code == 200
    assert client.post(f'/api/v1/ai/family/sync-memories/{a}', headers={'Authorization': ''}).status_code == 401
    assert client.post(f'/api/v1/ai/family/sync-memories/{a}', headers=second_user_headers).status_code == 403
    async def sync(**kwargs):
        assert kwargs['allowed_memorial_ids'] == {a}
        return {'checked': True}
    monkeypatch.setattr('app.api.ai.sync_family_memories', sync)
    r = client.post(f'/api/v1/ai/family/sync-memories/{a}', headers=auth_headers)
    assert r.status_code == 200 and r.json()['checked']


@pytest.mark.parametrize('decision', ['reject', 'cancel', 'accept'])
def test_transfer_without_retaining_editor_and_pending_links(client, auth_headers, second_user_headers, db_session, decision):
    owner = db_session.query(User).filter_by(email='test@example.com').one()
    child = db_session.query(User).filter_by(email='other@example.com').one()
    child.email_verified = True
    db_session.commit()
    a = make(client, auth_headers, 'Father')
    b = make(client, second_user_headers, 'Other memorial')
    request_id = link(client, auth_headers, a, b).json()['request_id']
    tid = client.post(f'/api/v1/memorials/{a}/ownership/transfer', headers=auth_headers,
                     json={'email': child.email, 'keep_editor': False}).json()['id']
    headers = auth_headers if decision == 'cancel' else second_user_headers
    assert client.post(f'/api/v1/memorials/ownership/transfers/{tid}/respond', headers=headers,
                       json={'decision': decision}).status_code == 200
    db_session.expire_all()
    if decision == 'accept':
        assert db_session.get(Memorial, a).owner_id == child.id
        assert db_session.query(MemorialAccess).filter_by(memorial_id=a, user_id=owner.id).first() is None
        from app.models import FamilyLinkRequest
        assert db_session.get(FamilyLinkRequest, request_id).status == 'cancelled'
    else:
        assert db_session.get(Memorial, a).owner_id == owner.id
    assert client.post(f'/api/v1/memorials/ownership/transfers/{tid}/respond', headers=headers,
                       json={'decision': decision}).status_code == 409


def test_removing_last_pair_link_clears_old_publication_choice(client, auth_headers):
    a = make(client, auth_headers, 'A')
    b = make(client, auth_headers, 'B')
    rid = link(client, auth_headers, a, b, public=False).json()['id']
    assert client.delete(f'/api/v1/family/relationships/{rid}', headers=auth_headers).status_code == 204
    assert link(client, auth_headers, a, b, public=True).status_code == 201
    assert len(client.get(f'/api/v1/family/memorials/{a}/full-tree', headers={'Authorization': ''}).json()['nodes']) == 2
