"""Authorship, guest archive privacy, and invitations after unsupported answers."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.models import Memory
from app.services.ai_tasks import generate_rag_response


def test_guest_cannot_read_archive_even_with_debug_shortcut(auth_client, client, memorial, db_session, monkeypatch):
    mid = memorial['id']
    auth_client.patch(f'/api/v1/memorials/{mid}', json={'is_public': True})
    db_session.add_all([
        Memory(memorial_id=mid, content='Approved private archive text', status='approved', contributor_name='Николай'),
        Memory(memorial_id=mid, content='Pending private archive text', status='pending', contributor_name='Катя'),
    ])
    db_session.commit()
    monkeypatch.setattr(settings, 'DEBUG', True)
    client.headers['Authorization'] = ''
    for suffix in ['/memories', '/memories?include_pending=true&q=private', '/timeline']:
        response = client.get(f'/api/v1/memorials/{mid}{suffix}')
        assert response.status_code == 200
        assert response.json() == []
    detail = client.get(f'/api/v1/memorials/{mid}').json()
    assert detail['memories'] == [] and detail['current_user_role'] is None
    assert 'private archive text' not in json.dumps(detail)


def test_author_survives_moderation_and_reaches_chat(auth_client, client, memorial, monkeypatch):
    import app.api.ai as api
    mid = memorial['id']
    owner_auth = client.headers['Authorization']
    auth_client.patch(f'/api/v1/memorials/{mid}', json={'is_public': True})
    client.headers['Authorization'] = ''
    response = client.post(f'/api/v1/memorials/{mid}/memories/public', json={
        'contributor_name': ' Николай ', 'content': 'Он ездил со мной на рыбалку. Мы поймали много рыбы.',
    })
    assert response.status_code == 201
    memory_id = response.json()['id']
    client.headers['Authorization'] = owner_auth
    assert client.get(f'/api/v1/memorials/{mid}/memories/pending').json()[0]['contributor_name'] == 'Николай'
    assert client.post(f'/api/v1/memorials/{mid}/memories/{memory_id}/approve').status_code == 200
    listed = client.get(f'/api/v1/memorials/{mid}/memories').json()
    assert listed[0]['contributor_name'] == 'Николай'
    assert len(client.get(f'/api/v1/memorials/{mid}/timeline').json()) == 1
    monkeypatch.setattr(api, 'get_embedding', AsyncMock(side_effect=RuntimeError('offline index')))
    generate = AsyncMock(return_value=('Мы с Николаем ездили на рыбалку.', [f'memory_{memory_id}']))
    monkeypatch.setattr(api, 'generate_rag_response', generate)
    chat = client.post('/api/v1/ai/avatar/chat', json={'memorial_id': mid, 'question': 'Что помнишь о рыбалке?'})
    assert chat.status_code == 200
    assert chat.json()['suggest_memory'] is False
    assert generate.call_args.kwargs['context_chunks'][0]['contributor_name'] == 'Николай'
    client.headers['Authorization'] = ''
    assert client.get(f'/api/v1/memorials/{mid}/memories').json() == []


def test_invite_uses_entered_name_instead_of_link_label(auth_client, client, memorial):
    mid = memorial['id']
    token = auth_client.post(f'/api/v1/invites/memorials/{mid}/create', json={'label': 'Для друзей'}).json()['token']
    client.headers['Authorization'] = ''
    response = client.post(f'/api/v1/memorials/{mid}/memories', params={'invite_token': token}, json={
        'content': 'Он ездил со мной на рыбалку.', 'contributor_name': 'Николай',
    })
    assert response.status_code == 201
    assert response.json()['contributor_name'] == 'Николай'
    assert response.json()['status'] == 'pending'


@pytest.mark.parametrize('has_memories', [False, True])
def test_no_evidence_invites_contribution(auth_client, memorial, db_session, monkeypatch, has_memories):
    import app.api.ai as api
    if has_memories:
        db_session.add(Memory(memorial_id=memorial['id'], content='Он любил шахматы.', status='approved', embedding_id='old'))
        db_session.commit()
    monkeypatch.setattr(api, 'get_embedding', AsyncMock(side_effect=RuntimeError('offline')))
    monkeypatch.setattr(api, 'generate_rag_response', AsyncMock(return_value=('Нет информации.', [])))
    response = auth_client.post('/api/v1/ai/avatar/chat', json={'memorial_id': memorial['id'], 'question': 'Что помнишь о рыбалке?'})
    assert response.status_code == 200
    assert response.json()['suggest_memory'] is True


@pytest.mark.asyncio
@pytest.mark.parametrize('language', ['ru', 'en'])
@pytest.mark.parametrize('supported', [True, False])
@pytest.mark.parametrize('shared_we', [False, True])
async def test_contributor_identity_in_generation_and_independent_verification(monkeypatch, language, supported, shared_we):
    import openai
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    quote = 'Он ездил со мной на рыбалку.' if language == 'ru' else 'He went fishing with me.'
    if shared_we:
        quote = 'Мы вместе ездили на рыбалку.' if language == 'ru' else 'We went fishing together.'
    answer = 'Мы с Николаем ездили на рыбалку.' if language == 'ru' else 'Nikolai and I went fishing.'
    author = 'Николай' if language == 'ru' else 'Nikolai'
    def completion(payload):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])
    create = AsyncMock(side_effect=[
        completion({'supported': True, 'answer': answer, 'excerpts': [{'memory_id': 7, 'quote': quote}]}),
        completion({'supported': supported}),
        completion({'supported': False}),
    ])
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    result, sources = await generate_rag_response('Что помнишь о рыбалке?' if language == 'ru' else 'What do you remember about fishing?',
        [{'memory_id': 7, 'text': quote, 'contributor_name': author}], memorial_name='Александр', language=language)
    first = create.call_args_list[0].kwargs['messages']
    assert 'CONTRIBUTOR IDENTITY' in first[0]['content']
    assert author in first[1]['content']
    verifier = create.call_args_list[1].kwargs['messages']
    assert 'ONLY if the quote explicitly describes' in verifier[0]['content']
    assert json.loads(verifier[1]['content'])['evidence'][0]['contributor_name'] == author
    assert bool(sources) is supported
    if supported:
        assert result == answer


@pytest.mark.parametrize('endpoint', ['public', 'invite'])
def test_whitespace_contributor_is_rejected(auth_client, client, memorial, endpoint):
    mid = memorial['id']
    params = {}
    if endpoint == 'public':
        auth_client.patch(f'/api/v1/memorials/{mid}', json={'is_public': True})
        path = f'/api/v1/memorials/{mid}/memories/public'
    else:
        token = auth_client.post(f'/api/v1/invites/memorials/{mid}/create', json={}).json()['token']
        params = {'invite_token': token}
        path = f'/api/v1/memorials/{mid}/memories'
    client.headers['Authorization'] = ''
    assert client.post(path, params=params, json={'content': 'Достаточно длинное воспоминание.', 'contributor_name': '   '}).status_code == 422
