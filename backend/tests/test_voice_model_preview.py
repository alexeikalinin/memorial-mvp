import pytest
from unittest.mock import AsyncMock
from app.models import Memorial


def test_model_comparison_reuses_voice_and_does_not_replace_clone(auth_client, memorial, db_session, monkeypatch):
    from app.api import ai
    m = db_session.get(Memorial, memorial['id'])
    m.voice_id = 'existing-clone'; m.voice_provider = 'fish_audio'
    db_session.commit()
    speech = AsyncMock(return_value=b'test-mp3')
    monkeypatch.setattr(ai, 'generate_speech', speech)
    for model in ['s2-pro', 's2.1-pro']:
        result = auth_client.post('/api/v1/ai/voice/preview', params={'memorial_id': m.id, 'model': model})
        assert result.status_code == 200, result.text
        assert result.content == b'test-mp3'
        assert result.headers['cache-control'] == 'no-store'
        assert speech.call_args.kwargs['voice_id'] == 'existing-clone'
        assert speech.call_args.kwargs['model'] == model
        assert speech.call_args.kwargs['speed'] == 1
    assert len({call.args[0] for call in speech.call_args_list}) == 1
    result = auth_client.patch('/api/v1/ai/voice/model', params={'memorial_id': m.id, 'model': 's2.1-pro'})
    assert result.status_code == 200
    db_session.refresh(m)
    assert m.voice_tts_model == 's2.1-pro'
    assert m.voice_id == 'existing-clone'
    assert auth_client.post('/api/v1/ai/voice/preview', params={'memorial_id': m.id, 'model': 'unknown'}).status_code == 422
    assert auth_client.get('/api/v1/ai/tts/status', params={'memorial_id': m.id}).json()['model'] == 's2.1-pro'


@pytest.mark.parametrize("selected,expected", [("s2.1-pro", "s2.1-pro"), ("s1", "s2-pro"), (None, "s2-pro")])
def test_fish_model_override_preserves_voice_reference(monkeypatch, selected, expected):
    import asyncio
    import httpx
    from unittest.mock import MagicMock
    from app.services import ai_tasks
    monkeypatch.setattr(ai_tasks.settings, 'FISH_AUDIO_API_KEY', 'offline-test')
    monkeypatch.setattr(ai_tasks.settings, 'FISH_AUDIO_MODEL', 's1')
    client = MagicMock()
    client.post = AsyncMock(return_value=httpx.Response(200, content=b'mp3'))
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=client)
    context.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(ai_tasks.httpx, 'AsyncClient', lambda: context)
    assert asyncio.run(ai_tasks.generate_speech('Test.', voice_id='same-voice', provider='fish_audio', model=selected)) == b'mp3'
    assert client.post.call_args.kwargs['headers']['model'] == expected
    assert client.post.call_args.kwargs['json']['reference_id'] == 'same-voice'


def test_retired_s1_cannot_be_selected_or_previewed(auth_client, memorial, db_session):
    from app.models import Memorial
    m = db_session.get(Memorial, memorial['id'])
    m.voice_id = 'existing-clone'
    m.voice_provider = 'fish_audio'
    m.voice_tts_model = 's1'
    db_session.commit()
    params = {'memorial_id': m.id, 'model': 's1'}
    assert auth_client.post('/api/v1/ai/voice/preview', params=params).status_code == 422
    assert auth_client.patch('/api/v1/ai/voice/model', params=params).status_code == 422
    assert auth_client.get('/api/v1/ai/tts/status', params={'memorial_id': m.id}).json()['model'] == 's2-pro'
    db_session.refresh(m)
    assert m.voice_id == 'existing-clone'


def test_legacy_s1_and_missing_selection_resolve_to_s2_pro():
    from app.services.voice_models import resolve_fish_model
    assert resolve_fish_model('s1', 's1') == 's2-pro'
    assert resolve_fish_model(None, 's1') == 's2-pro'
    assert resolve_fish_model(None, None) == 's2-pro'
    assert resolve_fish_model('s2-pro', 's2.1-pro') == 's2-pro'
    assert resolve_fish_model('s2.1-pro', 's1') == 's2.1-pro'
