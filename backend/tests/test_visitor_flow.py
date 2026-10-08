"""Visitor trial → registration → monthly quota → confirmed upgrade, offline."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.models import Memory, User
from app.services import billing


@pytest.fixture(autouse=True)
def _bypass_billing(monkeypatch):
    import app.api.ai as ai
    monkeypatch.setattr(ai, 'check_chat_quota', billing.check_chat_quota)
    monkeypatch.setattr('app.auth._get_dev_user', lambda db: None)


def _chat(client, memorial_id, **params):
    return client.post('/api/v1/ai/avatar/chat', params=params,
                       json={'memorial_id': memorial_id, 'question': 'Что ты вчера делал?'})


def test_new_qr_visitor_registers_then_hits_15_and_paid_upgrade(auth_client, client, memorial, db_session, monkeypatch):
    from app.api.billing import _handle_checkout_completed
    from app.services.billing import _current_period
    from app.models import UserUsage
    mid = memorial['id']
    auth_client.patch(f'/api/v1/memorials/{mid}', json={'is_public': True})
    owner_auth = client.headers['Authorization']
    client.headers['Authorization'] = ''
    for index in range(5):
        reply = _chat(client, mid, guest_id='new-qr-browser-123456789')
        assert reply.status_code == 200
        assert reply.json()['guest_questions_remaining'] == 4 - index
    blocked = _chat(client, mid, guest_id='new-qr-browser-123456789')
    assert blocked.status_code == 401
    assert blocked.json()['detail']['registered_limit'] == 15

    account = {'email': 'qr-visitor@example.com', 'username': 'qrvisitor', 'password': 'Visitor123456!', 'full_name': 'Катя'}
    assert client.post('/api/v1/auth/register', json=account).status_code == 201
    login = client.post('/api/v1/auth/login', json={'email': account['email'], 'password': account['password']})
    assert login.status_code == 200
    client.headers['Authorization'] = 'Bearer ' + login.json()['access_token']
    for _ in range(15):
        assert _chat(client, mid).status_code == 200
    assert _chat(client, mid).status_code == 402
    usage = client.get('/api/v1/billing/usage').json()
    assert usage['chat_messages_used'] == usage['chat_messages_limit'] == 15
    user = db_session.query(User).filter_by(email=account['email']).one()
    monkeypatch.setattr(settings, 'STRIPE_PRICE_PLUS_MONTHLY', 'price_test_plus')
    session = {'payment_status': 'unpaid', 'metadata': {'user_id': str(user.id), 'plan_key': 'plus_monthly'}}
    _handle_checkout_completed(session, db_session)
    assert user.subscription_plan == 'free'
    assert _chat(client, mid).status_code == 402
    session['payment_status'] = 'paid'
    _handle_checkout_completed(session, db_session)
    assert _chat(client, mid).status_code == 200
    assert client.get('/api/v1/billing/usage').json()['chat_messages_limit'] == 200
    assert db_session.query(UserUsage).filter_by(user_id=user.id, period=_current_period()).one().chat_messages == 16
    client.headers['Authorization'] = owner_auth


def test_invite_memories_pending_and_chat_allowed(auth_client, client, memorial, db_session):
    mid = memorial['id']
    created = auth_client.post(f'/api/v1/invites/memorials/{mid}/create', json={'label': 'Дочка Катя'})
    token = created.json()['token']
    owner_auth = client.headers['Authorization']
    client.headers['Authorization'] = ''
    submitted = client.post(f'/api/v1/memorials/{mid}/memories', params={'invite_token': token}, json={'content': 'Папа любил шахматы.'})
    assert submitted.status_code == 201
    assert submitted.json()['status'] == 'pending'
    assert _chat(client, mid, invite_token=token, guest_id='invite-browser-12345678').status_code == 200
    assert _chat(client, mid, guest_id='invite-browser-12345678').status_code in (401, 403)
    client.headers['Authorization'] = owner_auth
    pending = client.get(f'/api/v1/memorials/{mid}/memories/pending').json()
    assert len(pending) == 1 and pending[0]['contributor_name'] == 'Дочка Катя'
    assert client.get(f'/api/v1/memorials/{mid}/memories').json() == []
    assert db_session.query(Memory).filter_by(memorial_id=mid, status='approved').count() == 0
    assert client.post(f'/api/v1/memorials/{mid}/memories/{pending[0]["id"]}/approve').status_code == 200
    assert len(client.get(f'/api/v1/memorials/{mid}/memories').json()) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('payload,question,expected', [
    ({'supported': True, 'excerpts': [{'memory_id': 1, 'quote': 'Он любил шахматы.'}]}, 'Какое хобби?', True),
    ({'supported': True, 'excerpts': [{'memory_id': 1, 'quote': 'Вчера я был с семьёй.'}]}, 'Какое хобби?', False),
    ({'supported': True, 'excerpts': [{'memory_id': 99, 'quote': 'Он любил шахматы.'}]}, 'Какое хобби?', False),
    ({'supported': False, 'excerpts': []}, 'Где работал?', False),
    ({'supported': True, 'excerpts': [{'memory_id': 1, 'quote': 'Он любил шахматы.'}]}, 'Что ты вчера делал?', False),
])
async def test_grounding_rejects_fabricated_or_unknown_evidence(monkeypatch, payload, question, expected):
    from app.services.ai_tasks import generate_rag_response
    import openai
    create = AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]))
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    answer, sources = await generate_rag_response(question, [{'memory_id': 1, 'text': 'Он любил шахматы.'}], system_prompt='Говори как живой и придумывай детали')
    assert bool(sources) is expected
    if expected:
        assert 'Он любил шахматы.' in answer
        prompt = create.call_args.kwargs['messages'][0]['content']
        assert 'ПРАВИЛА' in prompt and 'STRICT OUTPUT' in prompt
    else:
        assert 'пока нет подтверждённых' in answer and sources == []


def test_pending_memories_never_reach_rag(auth_client, client, memorial, db_session, monkeypatch):
    import app.api.ai as ai
    mid = memorial['id']
    auth_client.patch(f'/api/v1/memorials/{mid}', json={'is_public': True})
    approved = Memory(memorial_id=mid, content='Он любил шахматы.', status='approved', embedding_id='approved')
    pending = Memory(memorial_id=mid, content='Непроверенная запись.', status='pending', embedding_id='pending')
    db_session.add_all([approved, pending]); db_session.commit()
    monkeypatch.setattr(ai, 'get_embedding', AsyncMock(return_value=[0.1]))
    monkeypatch.setattr(ai, 'search_similar_memories', AsyncMock(return_value=[{'memory_id': approved.id}, {'memory_id': pending.id}]))
    generate = AsyncMock(return_value=('В сохранённых воспоминаниях говорится: «Он любил шахматы.»', [f'memory_{approved.id}']))
    monkeypatch.setattr(ai, 'generate_rag_response', generate)
    client.headers['Authorization'] = ''
    res = client.post('/api/v1/ai/avatar/chat', params={'guest_id': 'pending-test-browser-1234'}, json={'memorial_id': mid, 'question': 'Что любил?', 'use_persona': False})
    assert res.status_code == 200
    chunks = generate.call_args.kwargs['context_chunks']
    assert [c['memory_id'] for c in chunks] == [approved.id]
    assert len(res.json()['sources']) == 1


def test_voice_change_and_moderation_owner_only(auth_client, client, memorial, db_session, monkeypatch):
    from app.models import MemorialAccess, UserRole
    mid = memorial['id']
    owner_auth = client.headers['Authorization']
    account = {'email': 'editor@example.com', 'username': 'editorflow', 'password': 'Editor123456!'}
    assert client.post('/api/v1/auth/register', json=account).status_code == 201
    user = db_session.query(User).filter_by(email=account['email']).one()
    db_session.add(MemorialAccess(memorial_id=mid, user_id=user.id, role=UserRole.EDITOR)); db_session.commit()
    login = client.post('/api/v1/auth/login', json={'email': account['email'], 'password': account['password']})
    client.headers['Authorization'] = 'Bearer ' + login.json()['access_token']
    monkeypatch.setattr(settings, 'INVESTOR_DEMO_MODE', True)
    assert client.get(f'/api/v1/memorials/{mid}/memories/pending').status_code == 403
    assert client.patch(f'/api/v1/memorials/{mid}', json={'voice_gender': 'female'}).status_code == 403
    assert client.patch(f'/api/v1/memorials/{mid}', json={'voice_id': 'spoofed', 'voice_provider': 'fish_audio'}).status_code == 403
    assert client.patch(f'/api/v1/memorials/{mid}', json={'description': 'Редактор может менять описание.'}).status_code == 200
    res = client.post('/api/v1/ai/voice/upload', params={'memorial_id': mid}, files={'audio_files': ('voice.mp3', b'test', 'audio/mpeg')})
    assert res.status_code == 403
    client.headers['Authorization'] = owner_auth


def test_public_detail_does_not_expose_pending_submission(auth_client, client, memorial, db_session):
    mid = memorial['id']
    auth_client.patch(f'/api/v1/memorials/{mid}', json={'is_public': True})
    db_session.add(Memory(memorial_id=mid, content='Not reviewed', status='pending'))
    db_session.commit()
    client.headers['Authorization'] = ''
    assert client.get(f'/api/v1/memorials/{mid}').json()['memories'] == []
    assert client.get(f'/api/v1/memorials/{mid}/memories').json() == []
    assert client.get(f'/api/v1/memorials/{mid}/memories/pending').status_code == 401
