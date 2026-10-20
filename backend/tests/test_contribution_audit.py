"""Regression checks replacing the former transcription defect reproductions."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.config import settings


def test_anonymous_transcription_is_rejected_before_provider(client, monkeypatch):
    import openai
    create = AsyncMock()
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kw: SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create))))
    response = client.post('/api/v1/ai/transcribe', headers={'Authorization': ''}, data={'language': 'en'}, files={'audio_file': ('recording.webm', b'fake-audio', 'audio/webm')})
    assert response.status_code == 401
    create.assert_not_awaited()


def test_authenticated_transcription_language_and_validation(auth_client, monkeypatch):
    import openai
    create = AsyncMock(return_value=SimpleNamespace(text='Recognized memory'))
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'offline-test')
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kw: SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create))))
    files = {'audio_file': ('recording.webm', b'fake-audio', 'audio/webm')}
    assert auth_client.post('/api/v1/ai/transcribe', data={'language': 'en'}, files=files).status_code == 200
    assert create.call_args.kwargs['language'] == 'en'
    assert auth_client.post('/api/v1/ai/transcribe?language=ru', files=files).status_code == 200
    assert create.call_args.kwargs['language'] == 'ru'
    assert auth_client.post('/api/v1/ai/transcribe', files={'audio_file': ('recording.webm', b'', 'audio/webm')}).status_code == 400
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', '')
    assert auth_client.post('/api/v1/ai/transcribe', files=files).status_code == 503
