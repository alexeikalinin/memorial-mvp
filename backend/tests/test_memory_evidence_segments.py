"""Original source evidence must survive spelling corrections in the answer."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.config import settings
from app.services.ai_tasks import generate_rag_response


def fake_provider(monkeypatch, responses):
    import openai
    complete = AsyncMock(side_effect=[SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(response)))]) for response in responses])
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=complete))))
    return complete


@pytest.mark.parametrize('language,source,answer', [
    ('ru', 'Мы вместе ловили пять карасей. Это было незабыаемо', 'Мы с Иваном ловили пять карасей. Это было незабываемо.'),
    ('en', 'We caught five fish together. It was unforgetable', 'Ivan and I caught five fish together. It was unforgettable.'),
])
def test_source_ids_preserve_original_typos_for_independent_verification(monkeypatch, language, source, answer):
    complete = fake_provider(monkeypatch, [
        {'supported': True, 'answer': answer, 'excerpts': [{'memory_id': 42, 'segment_ids': [1, 2]}]},
        {'supported': True},
    ])
    result = asyncio.run(generate_rag_response('Tell me about fishing' if language == 'en' else 'расскажи про рыбалку',
        [{'memory_id': 42, 'text': source, 'contributor_name': 'Иван', 'source_memorial_id': 8}], memorial_name='Андрей', language=language))
    assert result == (answer, ['memory_42'])
    evidence = json.loads(complete.call_args_list[1].kwargs['messages'][1]['content'])['evidence']
    assert evidence[1]['quote'] == source.split('. ')[1]
    assert all(item['quote'] in source for item in evidence)
    assert evidence[0]['contributor_name'] == 'Иван'
    prompt = complete.call_args_list[0].kwargs['messages'][1]['content']
    assert '[segment 1]' in prompt and '[segment 2]' in prompt


@pytest.mark.parametrize('indices', [[], [0], [-1], [2], [True], ['1'], [1.0], [1, 1], [1, 1, 1, 1], None])
def test_invalid_source_segment_ids_cannot_bypass_grounding(monkeypatch, indices):
    complete = fake_provider(monkeypatch, [{'supported': True, 'answer': 'Invented', 'excerpts': [{'memory_id': 42, 'segment_ids': indices}]}])
    answer, sources = asyncio.run(generate_rag_response('Fishing?', [{'memory_id': 42, 'text': 'We caught five fish.'}]))
    assert sources == []
    assert 'не могу найти' in answer
    assert complete.await_count == 1


def test_fabricated_memory_id_is_rejected(monkeypatch):
    complete = fake_provider(monkeypatch, [{'supported': True, 'answer': 'Invented', 'excerpts': [{'memory_id': 99, 'segment_ids': [1]}]}])
    assert asyncio.run(generate_rag_response('Fishing?', [{'memory_id': 42, 'text': 'We caught five fish.'}]))[1] == []
    assert complete.await_count == 1


def test_valid_segments_do_not_bypass_fact_checker(monkeypatch):
    complete = fake_provider(monkeypatch, [
        {'supported': True, 'answer': 'We caught fifty fish.', 'excerpts': [{'memory_id': 42, 'segment_ids': [1]}]},
        {'supported': False},
        {'supported': False},
    ])
    assert asyncio.run(generate_rag_response('Fishing?', [{'memory_id': 42, 'text': 'We caught five fish.'}]))[1] == []
    assert complete.await_count == 3


def test_legacy_modified_quote_is_still_rejected(monkeypatch):
    complete = fake_provider(monkeypatch, [{'supported': True, 'answer': 'Corrected.', 'excerpts': [{'memory_id': 42, 'quote': 'It was unforgettable.'}]}])
    assert asyncio.run(generate_rag_response('Fishing?', [{'memory_id': 42, 'text': 'It was unforgetable'}]))[1] == []
    assert complete.await_count == 1
