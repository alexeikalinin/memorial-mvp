from datetime import datetime, timedelta, timezone
import hashlib
from urllib.parse import urlsplit
from unittest.mock import AsyncMock

from jose import jwt
import pytest

from app.config import settings
from app.models import Memory, MemoryAudioReply
from app.services.recorded_reply import AUDIENCE, recorded_reply_url


@pytest.mark.parametrize('question', ['Скажи свою благодарственную речь',
    'Расскажи благодарственную речь для гостей',
    'Скажи благодарственную речь, гости уже пришли'])
def test_chat_uses_attached_recording_without_ai(auth_client, memorial, db_session, monkeypatch, question):
    import app.api.ai as api
    content = b'owner supplied mp3 bytes'
    speech = Memory(memorial_id=memorial['id'], title='Благодарственная речь гостям',
                    content='Спасибо всем, что пришли. Это полная речь.', status='approved')
    db_session.add(speech)
    db_session.flush()
    db_session.add(MemoryAudioReply(memory_id=speech.id, audio_data=content, file_name='speech.mp3',
                                   mime_type='audio/mpeg', sha256=hashlib.sha256(content).hexdigest()))
    db_session.commit()
    calls = {}
    for name in ['generate_speech', 'generate_rag_response', 'get_embedding', 'search_similar_memories', 'animate_photo_service']:
        calls[name] = AsyncMock(side_effect=AssertionError('No external AI for saved recording'))
        monkeypatch.setattr(api, name, calls[name])
    monkeypatch.setattr(api, 'check_tts_access', lambda user: None)
    response = auth_client.post('/api/v1/ai/avatar/chat', json={
        'memorial_id': memorial['id'], 'question': question, 'include_audio': True})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['answer'] == speech.content
    assert result['audio_error'] is None
    assert result['suggest_memory'] is False
    assert result['sources']
    assert result['audio_url'].startswith('http://testserver/api/v1/ai/recorded-reply/')
    url = urlsplit(result['audio_url'])
    playback = auth_client.get(url.path + '?' + url.query)
    assert playback.status_code == 200
    assert playback.content == content
    assert playback.headers['content-type'] == 'audio/mpeg'
    partial = auth_client.get(url.path + '?' + url.query, headers={'Range':'bytes=2-6'})
    assert partial.status_code == 206
    assert partial.content == content[2:7]
    assert partial.headers['content-range'] == f'bytes 2-6/{len(content)}'
    for mock in calls.values():
        mock.assert_not_awaited()


def test_recorded_audio_requires_matching_unexpired_playback_token(client):
    url = recorded_reply_url(10)
    assert client.get(url.replace('/10?', '/11?')).status_code == 403
    assert client.get('/api/v1/ai/recorded-reply/10?token=invalid').status_code == 403
    for audience, exp in [(AUDIENCE, datetime.now(timezone.utc)-timedelta(seconds=1)),
                          ('wrong-purpose', datetime.now(timezone.utc)+timedelta(hours=1))]:
        token = jwt.encode({'memory_id':10,'aud':audience,'exp':exp},settings.SECRET_KEY,algorithm=settings.ALGORITHM)
        assert client.get('/api/v1/ai/recorded-reply/10',params={'token':token}).status_code == 403


def test_removed_or_unapproved_recording_is_not_available(client, memorial, db_session):
    memory = Memory(memorial_id=memorial['id'],title='Благодарственная речь',content='Спасибо всем.',status='pending')
    db_session.add(memory)
    db_session.flush()
    db_session.add(MemoryAudioReply(memory_id=memory.id,audio_data=b'audio',file_name='speech.mp3',sha256='x'))
    db_session.commit()
    assert client.get(recorded_reply_url(memory.id)).status_code == 404
