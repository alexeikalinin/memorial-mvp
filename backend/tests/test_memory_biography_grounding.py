"""Biography/pronoun regression, with an opt-in synthetic real-model evaluation."""
import asyncio
import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.models import Memorial, Memory
from app.services.ai_tasks import generate_rag_response


RU_SOURCE = 'Орлова Мария родилась в Витебске 12 апреля 1955 года. В школьные годы она играла в волейбол.'
RU_ANSWER = 'Я родилась в Витебске 12 апреля 1955 года. В школьные годы я играла в волейбол.'
EN_SOURCE = 'Maria Orlova was born in York on 12 April 1955. At school she played volleyball.'
EN_ANSWER = 'I was born in York on 12 April 1955. At school I played volleyball.'


def completion(payload):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])


@pytest.mark.parametrize('language,subject,source,answer', [
    ('ru', 'Орлова Мария', RU_SOURCE, RU_ANSWER),
    ('en', 'Maria Orlova', EN_SOURCE, EN_ANSWER),
])
def test_approved_unindexed_biography_reaches_both_model_stages(
        auth_client, memorial, db_session, monkeypatch, language, subject, source, answer):
    import openai
    import app.api.ai as api
    db_session.get(Memorial, memorial['id']).name = subject
    memory = Memory(memorial_id=memorial['id'], content=source, status='approved',
                    contributor_name='Nikolai', embedding_id=None)
    db_session.add(memory)
    db_session.commit()
    memory_id = memory.id
    create = AsyncMock(side_effect=[
        completion({'supported': True, 'answer': answer,
                    'excerpts': [{'memory_id': memory_id, 'segment_ids': [1, 2]}]}),
        completion({'supported': True}),
    ])
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kw: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    embed = AsyncMock(side_effect=AssertionError('Overview must not depend on index state'))
    search = AsyncMock(side_effect=AssertionError('Overview must not depend on vector retrieval'))
    monkeypatch.setattr(api, 'get_embedding', embed)
    monkeypatch.setattr(api, 'search_similar_memories', search)
    response = auth_client.post('/api/v1/ai/avatar/chat', json={
        'memorial_id': memorial['id'], 'language': language,
        'question': 'что ты помнишь о себе?' if language == 'ru' else 'what do you remember about yourself?',
    })
    assert response.status_code == 200
    assert response.json()['answer'] == answer
    assert response.json()['sources']
    assert response.json()['suggest_memory'] is False
    assert create.await_count == 2
    payload = json.loads(create.call_args_list[1].kwargs['messages'][1]['content'])
    assert payload['memorial_subject'] == subject
    assert payload['candidate_answer'] == answer
    assert len(payload['evidence']) == 2
    assert all(item['source_text'] == source and item['contributor_name'] == 'Nikolai'
               for item in payload['evidence'])
    assert ' '.join(item['quote'] for item in payload['evidence']) == source
    embed.assert_not_awaited()
    search.assert_not_awaited()


def test_verifier_rejection_logs_stage_without_private_text(monkeypatch, caplog):
    import openai
    create = AsyncMock(side_effect=[
        completion({'supported': True, 'answer': 'Я родилась в 1900 году.',
                    'excerpts': [{'memory_id': 7, 'segment_ids': [1]}]}),
        completion({'supported': False}),
    ])
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kw: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    answer, sources = asyncio.run(generate_rag_response('Когда ты родилась?',
        [{'memory_id': 7, 'text': RU_SOURCE, 'contributor_name': 'Nikolai'}], memorial_name='Орлова Мария'))
    assert sources == []
    assert 'не могу найти' in answer
    assert 'rejected by factual verifier' in caplog.text
    assert 'memory_7' in caplog.text
    assert RU_SOURCE not in caplog.text and '1900' not in caplog.text


# Explicit opt-in only. All data below is fictional; the suite sends no DB content.
LIVE_CASES = [
    ('ru-biography', 'ru', 'Орлова Мария', RU_SOURCE, RU_ANSWER, True),
    ('en-biography', 'en', 'Maria Orlova', EN_SOURCE, EN_ANSWER, True),
    ('name-order', 'ru', 'Мария Орлова', RU_SOURCE, RU_ANSWER, True),
    ('typo', 'ru', 'Иван', 'Иван любил баскетбл.', 'Я любил баскетбол.', True),
    ('wrong-year', 'ru', 'Орлова Мария', RU_SOURCE, RU_ANSWER.replace('1955', '1900'), False),
    ('wrong-sport', 'en', 'Maria Orlova', EN_SOURCE, EN_ANSWER.replace('volleyball', 'football'), False),
    ('narrator-event', 'ru', 'Орлова Мария',
     'Орлова Мария родилась в Витебске. Я, Николай, играл в волейбол.', 'Я играла в волейбол.', False),
    ('invented-companion', 'en', 'Maria Orlova',
     'Maria Orlova liked fishing.', 'Nikolai and I went fishing together.', False),
    ('relative-event', 'ru', 'Орлова Мария',
     '[Из воспоминаний Анны (sister)]: Анна родилась в Витебске. Она играла в волейбол.',
     'Я родилась в Витебске. Я играла в волейбол.', False),
]


@pytest.mark.skipif(os.getenv('RUN_LIVE_GROUNDING') != '1', reason='Explicit real-model opt-in required')
@pytest.mark.parametrize('case_id,language,subject,source,answer,supported', LIVE_CASES, ids=[c[0] for c in LIVE_CASES])
def test_live_biography_fact_checker(monkeypatch, case_id, language, subject, source, answer, supported):
    import openai
    real_client = openai.AsyncOpenAI

    class CandidateThenRealVerifier:
        def __init__(self, **kwargs):
            self.client = real_client(**kwargs, timeout=30, max_retries=0)
            self.calls = 0
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        async def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return completion({'supported': True, 'answer': answer,
                                   'excerpts': [{'memory_id': 7, 'segment_ids': [1, 2] if '. ' in source else [1]}]})
            return await self.client.chat.completions.create(**kwargs)

    monkeypatch.setattr(openai, 'AsyncOpenAI', CandidateThenRealVerifier)
    result, sources = asyncio.run(generate_rag_response(
        'что ты помнишь о себе?' if language == 'ru' else 'what do you remember about yourself?',
        [{'memory_id': 7, 'text': source, 'contributor_name': 'Nikolai', 'source_memorial_id': 9}],
        memorial_name=subject, language=language))
    assert bool(sources) is supported, case_id
    if supported:
        assert result == answer
