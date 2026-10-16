"""A rejected draft can be repaired, but never returned without verification."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.services.ai_tasks import generate_rag_response


def completion(payload):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])


@pytest.mark.parametrize('second_supported', [True, False])
def test_rejected_overview_is_regenerated_and_independently_checked(monkeypatch, second_supported):
    import openai
    first = {'supported': True, 'answer': 'Я родилась в Минске и работала врачом.',
             'excerpts': [{'memory_id': 7, 'segment_ids': [1]}]}
    repaired = {'supported': True, 'answer': 'Я родилась в Минске.',
                'excerpts': [{'memory_id': 7, 'segment_ids': [1]}]}
    create = AsyncMock(side_effect=[completion(first), completion({'supported': False}),
                                   completion(repaired), completion({'supported': second_supported})])
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kw: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    answer, sources = asyncio.run(generate_rag_response('что ты помнишь о себе?',
        [{'memory_id': 7, 'text': 'Анна родилась в Минске.'}], memorial_name='Анна'))
    assert create.await_count == 4
    assert 'работала врачом' not in answer
    if second_supported:
        assert answer == repaired['answer'] and sources == ['memory_7']
    else:
        assert sources == [] and 'не могу найти' in answer
    checked = json.loads(create.call_args_list[3].kwargs['messages'][1]['content'])
    assert checked['candidate_answer'] == repaired['answer']
    assert checked['evidence'][0]['quote'] == 'Анна родилась в Минске.'


def test_fabricated_repair_source_is_rejected_before_verifier(monkeypatch):
    import openai
    draft = {'supported': True, 'answer': 'Я была врачом.',
             'excerpts': [{'memory_id': 7, 'segment_ids': [1]}]}
    bad_repair = {'supported': True, 'answer': 'Я была врачом.',
                  'excerpts': [{'memory_id': 999, 'segment_ids': [1]}]}
    create = AsyncMock(side_effect=[completion(draft), completion({'supported': False}), completion(bad_repair)])
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kw: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    answer, sources = asyncio.run(generate_rag_response('Кем ты работала?',
        [{'memory_id': 7, 'text': 'Анна родилась в Минске.'}], memorial_name='Анна'))
    assert sources == [] and 'не могу найти' in answer
    assert create.await_count == 3
