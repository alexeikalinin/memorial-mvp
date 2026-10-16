import io
import wave
from unittest.mock import AsyncMock
import pytest
from app.models import Memorial, MemorialVoice


def sample(value):
    data = io.BytesIO()
    with wave.open(data, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(value.to_bytes(2, 'little') * 16000)
    return data.getvalue()


def upload(client, mid, value=10, name='sample.wav'):
    return client.post(f'/api/v1/ai/voice/upload?memorial_id={mid}',
                       files=[('audio_files', (name, sample(value), 'audio/wav'))], data={'provider': 'fish_audio'})


def test_new_candidate_preserves_active_and_reuses_identical_audio(auth_client, memorial, db_session, monkeypatch, tmp_path):
    from app.api import ai
    monkeypatch.chdir(tmp_path)
    m = db_session.get(Memorial, memorial['id'])
    m.voice_id = 'old'; m.voice_provider = 'fish_audio'; db_session.commit()
    clone = AsyncMock(return_value='new')
    delete = AsyncMock()
    monkeypatch.setattr(ai, 'create_custom_voice', clone)
    monkeypatch.setattr(ai, 'delete_custom_voice', delete)
    result = upload(auth_client, m.id)
    assert result.status_code == 200, result.text
    assert not result.json()['active']
    db_session.refresh(m)
    assert m.voice_id == 'old'
    assert clone.await_count == 1 and delete.await_count == 0
    again = upload(auth_client, m.id, name='renamed.wav')
    assert again.status_code == 200 and again.json()['reused']
    assert clone.await_count == 1
    versions = auth_client.get('/api/v1/ai/voice/versions', params={'memorial_id': m.id}).json()['voices']
    assert len(versions) == 2 and sum(v['active'] for v in versions) == 1
    new = next(v for v in versions if not v['active'])
    assert auth_client.patch(f'/api/v1/ai/voice/versions/{new["id"]}/select', params={'memorial_id': m.id}).status_code == 200
    db_session.refresh(m)
    assert m.voice_id == 'new'
    old = next(v for v in versions if v['active'])
    auth_client.patch(f'/api/v1/ai/voice/versions/{old["id"]}/select', params={'memorial_id': m.id})
    db_session.refresh(m)
    assert m.voice_id == 'old' and clone.await_count == 1
    assert not list((tmp_path/'uploads/voices').iterdir())


def test_first_candidate_selected_and_preview_cached_without_selecting_another(auth_client, memorial, db_session, monkeypatch, tmp_path):
    from app.api import ai
    monkeypatch.chdir(tmp_path)
    clone = AsyncMock(side_effect=['first', 'second'])
    speech = AsyncMock(return_value=b'mp3-preview')
    monkeypatch.setattr(ai, 'create_custom_voice', clone)
    monkeypatch.setattr(ai, 'generate_speech', speech)
    first = upload(auth_client, memorial['id']).json()
    assert first['active']
    second = upload(auth_client, memorial['id'], 20).json()
    params = {'memorial_id': memorial['id'], 'version_id': second['version_id'], 'model':'s2-pro'}
    for _ in range(2):
        response = auth_client.post('/api/v1/ai/voice/preview', params=params)
        assert response.status_code == 200 and response.content == b'mp3-preview'
    assert speech.await_count == 1
    assert speech.call_args.kwargs['voice_id'] == 'second'
    assert db_session.get(Memorial, memorial['id']).voice_id == 'first'


def test_candidate_cannot_be_used_or_previewed_on_another_memorial(auth_client, memorial, db_session, monkeypatch):
    other = auth_client.post('/api/v1/memorials/', json={'name':'Other'}).json()
    row = MemorialVoice(memorial_id=memorial['id'], name='private', voice_id='secret', provider='fish_audio', state='ready')
    db_session.add(row); db_session.commit()
    params = {'memorial_id':other['id']}
    assert auth_client.patch(f'/api/v1/ai/voice/versions/{row.id}/select',params=params).status_code == 404
    assert auth_client.post('/api/v1/ai/voice/preview',params={**params,'version_id':row.id,'model':'s2-pro'}).status_code == 404


def test_failed_attempt_not_retried_and_old_voice_kept(auth_client, memorial, db_session, monkeypatch, tmp_path):
    from app.api import ai
    monkeypatch.chdir(tmp_path)
    m = db_session.get(Memorial, memorial['id']);m.voice_id='old';m.voice_provider='fish_audio';db_session.commit()
    clone = AsyncMock(side_effect=ValueError('provider failed'))
    monkeypatch.setattr(ai,'create_custom_voice',clone)
    assert upload(auth_client,m.id).status_code == 400
    assert upload(auth_client,m.id).status_code == 409
    assert clone.await_count == 1 and m.voice_id == 'old'
    assert not list((tmp_path/'uploads/voices').iterdir())
