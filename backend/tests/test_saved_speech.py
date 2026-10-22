from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models import Memory
from app.services.saved_speech import requested_thank_you_speech


@pytest.mark.parametrize('question', [
    'Скажи свою благодарственную речь',
    'Скажи свою благодарственную речь, гости уже собрались',
    'Скажи свою благодарственную речь, гости уже пришли',
    'Зачитай благодарственную речь целиком сегодня',
])
def test_saved_speech_full_text_reaches_response_and_tts(
        auth_client, memorial, db_session, monkeypatch, tmp_path, question):
    import app.api.ai as api
    from app.config import settings
    text = 'Здравствуйте, родные.\n\n' + 'Спасибо, что пришли. ' * 120 + '\nМоя душа с вами навсегда.'
    memory = Memory(memorial_id=memorial['id'], title='Благодарственная речь гостям на годовщину',
                    content=text, status='approved', contributor_name='Другой автор')
    db_session.add(memory)
    db_session.commit()
    memory_id = memory.id
    db_session.add(Memory(memorial_id=memorial['id'], title='Благодарственная речь',
                          content='НЕОДОБРЕННЫЙ ТЕКСТ', status='pending'))
    db_session.commit()
    embed = AsyncMock(side_effect=AssertionError('No embedding needed for reading'))
    search = AsyncMock(side_effect=AssertionError('No retrieval needed for reading'))
    generate = AsyncMock(side_effect=AssertionError('Saved speech must not be summarized'))
    speech = AsyncMock(return_value=b'test-audio')
    monkeypatch.setattr(api, 'get_embedding', embed)
    monkeypatch.setattr(api, 'search_similar_memories', search)
    monkeypatch.setattr(api, 'generate_rag_response', generate)
    monkeypatch.setattr(api, 'generate_speech', speech)
    monkeypatch.setattr(api, '_resolve_tts_voice', lambda m: ('test-voice', 'fish_audio'))
    monkeypatch.setattr(settings, 'FISH_AUDIO_API_KEY', 'offline-test')
    monkeypatch.setattr(settings, 'USE_S3', False)
    monkeypatch.setattr(api, 'check_tts_access', lambda user: None)
    (tmp_path / 'uploads').mkdir()
    monkeypatch.chdir(tmp_path)
    response = auth_client.post('/api/v1/ai/avatar/chat', json={
        'memorial_id': memorial['id'], 'question': question, 'include_audio': True,
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['answer'] == text
    assert body['suggest_memory'] is False
    assert len(body['sources']) == 1
    assert f'#{memory_id}' in body['sources'][0]
    assert body['audio_url']
    assert speech.call_args.args[0] == text
    embed.assert_not_awaited()
    search.assert_not_awaited()
    generate.assert_not_awaited()


@pytest.mark.parametrize('question', [
    'О чем твоя благодарственная речь?', 'Скажи благодарственную речь кратко',
    'Придумай благодарственную речь', 'Не прочитай благодарственную речь',
    'Когда ты произнес благодарственную речь?',
])
def test_other_requests_use_normal_chat(question):
    memory = SimpleNamespace(status='approved', title='Благодарственная речь', content='Полный текст')
    assert requested_thank_you_speech(question, [memory]) is None


def test_missing_pending_or_ambiguous_speech_is_not_selected():
    approved = SimpleNamespace(status='approved', title='Благодарственная речь', content='Текст')
    pending = SimpleNamespace(status='pending', title='Благодарственная речь', content='Секрет')
    question = 'Скажи свою благодарственную речь'
    for memories in [[], [pending], [approved, approved]]:
        assert requested_thank_you_speech(question, memories) is None
