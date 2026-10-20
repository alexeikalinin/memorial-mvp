from types import SimpleNamespace
from unittest.mock import AsyncMock


def test_transcription_requires_real_auth(client):
    result = client.post('/api/v1/ai/transcribe', headers={'Authorization': ''}, files={'audio_file': ('voice.mp4', b'audio', 'audio/mp4')})
    assert result.status_code == 401


def test_invited_safari_recording_language_and_revocation(auth_client, client, memorial, monkeypatch):
    import openai
    from app.api.ai import settings
    create = AsyncMock(return_value=SimpleNamespace(text='Мы с Николаем ездили на рыбалку.'))
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', 'synthetic-test-key')
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create))))
    invite = auth_client.post(f"/api/v1/invites/memorials/{memorial['id']}/create", json={'label': 'Recording', 'permissions': {'add_memories': True}}).json()
    data = {'memorial_id': str(memorial['id']), 'invite_token': invite['token'], 'language': 'en'}
    files = {'audio_file': ('voice.mp4', b'synthetic-mp4', 'audio/mp4')}
    result = client.post('/api/v1/ai/transcribe', headers={'Authorization': ''}, data=data, files=files)
    assert result.status_code == 200, result.text
    assert result.json()['language'] == 'en'
    assert create.call_args.kwargs == {'model': 'whisper-1', 'file': ('recording.mp4', b'synthetic-mp4'), 'language': 'en'}
    data['memorial_id'] = str(memorial['id'] + 100)
    assert client.post('/api/v1/ai/transcribe', headers={'Authorization': ''}, data=data, files=files).status_code == 403
    data['memorial_id'] = str(memorial['id'])
    data['invite_token'] = 'revoked-or-unknown'
    assert client.post('/api/v1/ai/transcribe', headers={'Authorization': ''}, data=data, files=files).status_code == 403
    assert create.await_count == 1


def test_recording_validation_precedes_provider(auth_client, memorial):
    data = {'memorial_id': str(memorial['id'])}
    for filename, body, expected in [('empty.wav', b'', 400), ('bad.exe', b'audio', 400), ('large.wav', b'x' * (25 * 1024 * 1024 + 1), 413)]:
        result = auth_client.post('/api/v1/ai/transcribe', data=data, files={'audio_file': (filename, body)})
        assert result.status_code == expected, result.text
