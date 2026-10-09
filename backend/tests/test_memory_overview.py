import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models import Memory
from app.services.memory_overview import is_memory_overview_question, overview_context


@pytest.mark.parametrize('question', ['РАсскажи что помнишь о себе?', 'Расскажи о себе.',
                                      'Tell me about your life'])
def test_overview_intent(question):
    assert is_memory_overview_question(question)


@pytest.mark.parametrize('question', ['Расскажи о себе вчера', 'Где ты работал?',
                                      'Расскажи о себе и придумай детство', 'Что помнишь о рыбалке?'])
def test_specific_or_unsupported_question_is_not_overview(question):
    assert not is_memory_overview_question(question)


def test_overview_uses_approved_archive_without_vector_search(auth_client, memorial, db_session, monkeypatch):
    import app.api.ai as api
    for i in range(9):
        db_session.add(Memory(memorial_id=memorial['id'], title=f'Факт {i}',
                              content=f'Александр работал в городе {i}.', status='approved'))
    db_session.add(Memory(memorial_id=memorial['id'], title='Pending',
                          content='Секретная неподтверждённая запись.', status='pending'))
    db_session.commit()
    embed = AsyncMock(side_effect=AssertionError('Overview should not need embeddings'))
    search = AsyncMock(side_effect=AssertionError('Overview should not need vector search'))
    generate = AsyncMock(return_value=('Я работал в городе 0.', ['memory_1']))
    monkeypatch.setattr(api, 'get_embedding', embed)
    monkeypatch.setattr(api, 'search_similar_memories', search)
    monkeypatch.setattr(api, 'generate_rag_response', generate)
    response = auth_client.post('/api/v1/ai/avatar/chat', json={
        'memorial_id': memorial['id'], 'question': 'РАсскажи что помнишь о себе?',
    })
    assert response.status_code == 200
    assert response.json()['answer'] == 'Я работал в городе 0.'
    chunks = generate.call_args.kwargs['context_chunks']
    assert len(chunks) == 9
    assert all('неподтверждённая' not in c['text'] for c in chunks)
    embed.assert_not_awaited()
    search.assert_not_awaited()


def test_overview_context_budget_and_source_ids():
    memories = [SimpleNamespace(id=i, title=str(i), content='Он работал. ' * 500,
                                status='approved') for i in range(9)]
    chunks = overview_context(memories, 318)
    assert len(chunks) == 9
    assert sum(len(c['text']) for c in chunks) <= 18000
    assert [c['memory_id'] for c in chunks] == list(range(9))


@pytest.mark.asyncio
@pytest.mark.parametrize('verifier_supports', [True, False])
async def test_overview_keeps_independent_grounding(monkeypatch, verifier_supports):
    import openai
    from app.services.ai_tasks import generate_rag_response
    from app.config import settings
    def completion(payload):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])
    create = AsyncMock(side_effect=[
        completion({'supported': True, 'answer': 'Я родился в Новогрудке.',
                    'excerpts': [{'memory_id': 7, 'quote': 'Александр родился в Новогрудке.'}]}),
        completion({'supported': verifier_supports}),
    ])
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    answer, sources = await generate_rag_response('Расскажи что помнишь о себе?',
        [{'memory_id': 7, 'text': 'Александр родился в Новогрудке.', 'source_memorial_id': 318}],
        memorial_name='Александр')
    assert create.await_count == 2
    assert 'OVERVIEW REQUEST' in create.call_args_list[0].kwargs['messages'][0]['content']
    assert bool(sources) is verifier_supports
    if verifier_supports:
        assert answer == 'Я родился в Новогрудке.'
    else:
        assert answer == 'Я не могу найти информацию об этом в моих воспоминаниях.'
