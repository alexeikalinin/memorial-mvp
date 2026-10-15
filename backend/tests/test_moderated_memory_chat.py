"""Guest submission -> moderation -> chat context, including index failures."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from app.config import settings

import pytest

from app.models import Memory


@pytest.mark.parametrize('index_state', ['stale', 'empty', 'unavailable', 'embedding_unavailable'])
def test_guest_fishing_memory_reaches_chat_after_approval(
    auth_client, client, memorial, db_session, monkeypatch, index_state,
):
    import openai
    import app.api.ai as api
    import app.services.ai_tasks as tasks
    from app.workers.worker import create_memory_embedding_task

    monkeypatch.setattr('app.auth._get_dev_user', lambda db: None)
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    mid = memorial['id']
    old = Memory(memorial_id=mid, content='Он любил шахматы.', status='approved', embedding_id='old-vector')
    db_session.add(old)
    db_session.commit()
    token = auth_client.post(f'/api/v1/invites/memorials/{mid}/create', json={'label': 'Другой телефон'}).json()['token']
    owner_header = client.headers['Authorization']
    client.headers['Authorization'] = ''
    fishing = 'Он любил рыбалку и ловил щуку на озере Нарочь.'
    submitted = client.post(f'/api/v1/memorials/{mid}/memories', params={'invite_token': token}, json={'title': 'Рыбалка', 'content': fishing})
    assert submitted.status_code == 201
    memory_id = submitted.json()['id']
    assert submitted.json()['status'] == 'pending'
    client.headers['Authorization'] = owner_header
    assert [m['id'] for m in client.get(f'/api/v1/memorials/{mid}/memories/pending').json()] == [memory_id]
    hits = [{'memory_id': old.id, 'score': .8, 'source_memorial_id': mid}] if index_state == 'stale' else []
    monkeypatch.setattr(api, 'get_embedding', AsyncMock(side_effect=RuntimeError('embedding down')) if index_state == 'embedding_unavailable' else AsyncMock(return_value=[.1]))
    monkeypatch.setattr(api, 'search_similar_memories', AsyncMock(side_effect=RuntimeError('index down')) if index_state == 'unavailable' else AsyncMock(return_value=hits))
    monkeypatch.setattr(tasks, 'upsert_memory_embedding', AsyncMock(side_effect=RuntimeError('index not ready')))
    contexts = []

    async def generate(**kwargs):
        chunks = kwargs['context_chunks']
        contexts.append(chunks)
        return await tasks.generate_rag_response(**kwargs)

    async def completion(**kwargs):
        prompt = '\n'.join(message['content'] for message in kwargs['messages'])
        if 'STRICT OUTPUT' in prompt:
            data = ({'supported': True, 'answer': 'Я ловил щуку на озере Нарочь.',
                     'excerpts': [{'memory_id': memory_id, 'quote': fishing}]}
                    if fishing in prompt else {'supported': False})
        else:
            data = {'supported': True}
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(data)))])

    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=completion))))
    monkeypatch.setattr(api, 'generate_rag_response', generate)
    payload = {'memorial_id': mid, 'question': 'Что он ловил на рыбалке?', 'use_persona': False}
    before = client.post('/api/v1/ai/avatar/chat', json=payload)
    assert before.status_code == 200
    assert not before.json()['sources']
    assert all(c['memory_id'] != memory_id for c in contexts[-1])
    enqueue = Mock(side_effect=RuntimeError('broker unavailable'))
    monkeypatch.setattr(create_memory_embedding_task, 'delay', enqueue)
    approved = client.post(f'/api/v1/memorials/{mid}/memories/{memory_id}/approve')
    assert approved.status_code == 200 and approved.json()['status'] == 'approved'
    enqueue.assert_called_once()
    assert client.get(f'/api/v1/memorials/{mid}/memories/pending').json() == []
    assert memory_id in [m['id'] for m in client.get(f'/api/v1/memorials/{mid}/memories').json()]
    assert client.post(f'/api/v1/memorials/{mid}/memories/{memory_id}/approve').status_code == 200
    enqueue.assert_called_once()
    after = client.post('/api/v1/ai/avatar/chat', json=payload)
    assert after.status_code == 200, after.text
    assert 'Нарочь' in after.json()['answer']
    assert any(f'#{memory_id}' in source for source in after.json()['sources'])
