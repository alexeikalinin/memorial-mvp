import asyncio
import io
import shutil
import subprocess
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile, Headers
from app.services.voice_samples import prepare_voice_samples

pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='FFmpeg required')


def upload(data, name, mime):
    return UploadFile(io.BytesIO(data), filename=name, headers=Headers({'content-type': mime}))


@pytest.fixture
def video(tmp_path):
    path = tmp_path / 'voice.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=32x32:d=1', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', '-c:v', 'mpeg4', '-c:a', 'aac', '-shortest', str(path)], check=True)
    return path.read_bytes()


def test_mp4_becomes_audio_only_and_source_is_deleted(tmp_path, video):
    paths = asyncio.run(prepare_voice_samples([upload(video, 'VOICE.MP4', 'video/mp4')], tmp_path / 'samples'))
    assert len(paths) == 1 and paths[0].suffix == '.mp3'
    assert list((tmp_path / 'samples').iterdir()) == paths
    result = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(paths[0])])
    assert result.strip() == b'audio'


def test_existing_audio_is_preserved(tmp_path):
    paths = asyncio.run(prepare_voice_samples([upload(b'audio sample', 'voice.ogg', 'audio/ogg')], tmp_path))
    assert paths[0].read_bytes() == b'audio sample'


def test_video_without_sound_fails_and_cleans_all_samples(tmp_path):
    silent = tmp_path / 'silent.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=32x32:d=1', '-c:v', 'mpeg4', str(silent)], check=True)
    samples = tmp_path / 'samples'
    with pytest.raises(ValueError, match='нет аудиодорожки'):
        asyncio.run(prepare_voice_samples([upload(b'audio', 'voice.wav', 'audio/wav'), upload(silent.read_bytes(), 'silent.mp4', 'video/mp4')], samples))
    assert not list(samples.iterdir())


def test_corrupt_video_is_rejected_and_removed(tmp_path):
    with pytest.raises(ValueError, match='Не удалось прочитать'):
        asyncio.run(prepare_voice_samples([upload(b'not a video', 'voice.mp4', 'video/mp4')], tmp_path))
    assert not list(tmp_path.iterdir())


def test_size_limit_cleans_partial_file(tmp_path, monkeypatch):
    monkeypatch.setattr('app.services.voice_samples.MAX_SAMPLE_BYTES', 3)
    with pytest.raises(ValueError, match='100 МБ'):
        asyncio.run(prepare_voice_samples([upload(b'1234', 'voice.wav', 'audio/wav')], tmp_path))
    assert not list(tmp_path.iterdir())


def test_upload_endpoint_sends_extracted_audio_to_provider(auth_client, memorial, video, monkeypatch, tmp_path):
    from app.api import ai
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ai, 'check_tts_access', lambda user: None)
    captured = []
    async def clone(audio_file_paths, **kwargs):
        captured.extend(audio_file_paths)
        assert all(Path(p).suffix == '.mp3' and Path(p).stat().st_size > 0 for p in audio_file_paths)
        return 'video-test-voice'
    monkeypatch.setattr(ai, 'create_custom_voice', clone)
    response = auth_client.post(f'/api/v1/ai/voice/upload?memorial_id={memorial["id"]}', files=[('audio_files', ('voice.mp4', video, 'video/mp4'))], data={'provider': 'fish_audio'})
    assert response.status_code == 200, response.text
    assert response.json()['voice_id'] == 'video-test-voice'
    assert response.json()['voice_provider'] == 'fish_audio'
    assert captured and not any(Path(p).exists() for p in captured)


def test_preview_returns_audio_without_cloning_and_removes_temp_files(auth_client, monkeypatch, tmp_path, video):
    from app.api import ai
    monkeypatch.chdir(tmp_path)
    async def forbidden(*args, **kwargs):
        pytest.fail('Preview must not create a paid voice model')
    monkeypatch.setattr(ai, 'create_custom_voice', forbidden)
    memorial = auth_client.post('/api/v1/memorials/', json={'name': 'Preview test'}).json()
    response = auth_client.post(f'/api/v1/ai/voice/prepare?memorial_id={memorial["id"]}', files={'audio_file': ('voice.mp4', video, 'video/mp4')})
    assert response.status_code == 200, response.text
    assert response.headers['content-type'].startswith('audio/mpeg')
    assert response.headers['cache-control'] == 'no-store'
    assert len(response.content) > 1000
    assert not list((tmp_path / 'uploads/voices').iterdir())
    assert not auth_client.get(f'/api/v1/memorials/{memorial["id"]}').json().get('voice_id')


def test_corrupt_preview_returns_error_and_cleans(auth_client, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    memorial = auth_client.post('/api/v1/memorials/', json={'name': 'Corrupt preview'}).json()
    response = auth_client.post(f'/api/v1/ai/voice/prepare?memorial_id={memorial["id"]}', files={'audio_file': ('voice.wav', b'broken', 'audio/wav')})
    assert response.status_code == 400
    assert not list((tmp_path / 'uploads/voices').iterdir())


def test_pronunciation_only_changes_spoken_text_and_passes_speed(monkeypatch):
    from app.services import ai_tasks
    captured = {}
    async def speech(text, voice_id=None, speed=1):
        captured.update(text=text, speed=speed, voice_id=voice_id)
        return b'audio'
    monkeypatch.setattr(ai_tasks, 'generate_speech_fish_audio', speech)
    original = 'Сачко здесь. Сачков там.'
    assert asyncio.run(ai_tasks.generate_speech(original, 'voice', 'fish_audio', .85, {'Сачко': 'Сачкó'})) == b'audio'
    assert captured == {'text': 'Сачкó здесь.\n\nСачков там.', 'speed': .85, 'voice_id': 'voice'}
    assert original == 'Сачко здесь. Сачков там.'


def test_speech_controls_are_bounded():
    from app.schemas import AvatarChatRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AvatarChatRequest(memorial_id=1, question='Hi', speech_speed=4)
    with pytest.raises(ValidationError):
        AvatarChatRequest(memorial_id=1, question='Hi', pronunciations={str(i): 'word' for i in range(21)})
