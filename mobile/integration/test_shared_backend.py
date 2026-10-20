"""Two independent device sessions share the existing API, ACL and stored materials."""
import io
import wave
import subprocess

from fastapi.testclient import TestClient
from PIL import Image


def device_session():
    from app.main import app
    mobile = TestClient(app)
    response = mobile.post('/api/v1/auth/login', json={'email': 'test@example.com', 'password': 'testpassword123'})
    assert response.status_code == 200
    mobile.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return mobile


def test_bidirectional_pages_memories_media_and_profile(auth_client):
    mobile = device_session()
    page = mobile.post('/api/v1/memorials/', json={'name': 'Мобильная проверка', 'is_public': False})
    assert page.status_code == 201, page.text
    mid = page.json()['id']
    assert mid in [p['id'] for p in auth_client.get('/api/v1/memorials/').json()]
    assert mobile.get('/api/v1/auth/me').json()['id'] == auth_client.get('/api/v1/auth/me').json()['id']
    for sender, receiver, text in [(mobile, auth_client, 'История добавлена с телефона.'),
                                    (auth_client, mobile, 'История добавлена с компьютера.')]:
        saved = sender.post(f'/api/v1/memorials/{mid}/memories', json={'title': 'Проверка', 'content': text})
        assert saved.status_code == 201, saved.text
        assert any(m['content'] == text for m in receiver.get(f'/api/v1/memorials/{mid}/memories').json())
    image = io.BytesIO()
    Image.new('RGB', (160, 160), (200, 160, 120)).save(image, format='PNG')
    audio = io.BytesIO()
    with wave.open(audio, 'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000); wav.writeframes(b'\x00\x00' * 1600)
    for sender, receiver, name, contents, mime, media_type in [
        (mobile, auth_client, 'семья.png', image.getvalue(), 'image/png', 'photo'),
        (auth_client, mobile, 'воспоминание.wav', audio.getvalue(), 'audio/wav', 'audio')]:
        saved = sender.post(f'/api/v1/memorials/{mid}/media/upload', files={'file': (name, contents, mime)})
        assert saved.status_code == 201, saved.text
        media = saved.json()
        assert media['media_type'] == media_type
        assert media['id'] in [m['id'] for m in receiver.get(f'/api/v1/memorials/{mid}/media').json()]
        download = receiver.get(f"/api/v1/media/{media['id']}")
        assert download.status_code == 200
        assert download.content == contents
    assert len(mobile.get(f'/api/v1/memorials/{mid}').json()['memories']) == 2
    changed = auth_client.patch(f'/api/v1/memorials/{mid}', json={'description': 'Изменено в вебе'})
    assert changed.status_code == 200
    assert mobile.get(f'/api/v1/memorials/{mid}').json()['description'] == 'Изменено в вебе'


def test_separate_account_cannot_read_private_page_and_viewer_cannot_write(auth_client, second_user_headers):
    page = auth_client.post('/api/v1/memorials/', json={'name': 'Закрытая страница'}).json()
    from app.main import app
    other = TestClient(app, headers=second_user_headers)
    mid = page['id']
    assert other.get(f'/api/v1/memorials/{mid}').status_code == 403
    grant = auth_client.post(f'/api/v1/memorials/{mid}/access', json={'email': 'other@example.com', 'role': 'viewer'})
    assert grant.status_code == 201, grant.text
    assert other.get(f'/api/v1/memorials/{mid}').json()['current_user_role'] == 'viewer'
    assert other.post(f'/api/v1/memorials/{mid}/memories', json={'content': 'Нельзя записать'}).status_code == 403
    assert other.post(f'/api/v1/memorials/{mid}/media/upload', files={'file': ('x.wav', b'audio', 'audio/wav')}).status_code == 403
    assert other.get(f'/api/v1/memorials/{mid}/memories/pending').status_code == 403


def test_guest_submission_is_pending_until_owner_approves(auth_client):
    page = auth_client.post('/api/v1/memorials/', json={'name': 'Публичная страница', 'is_public': True}).json()
    from app.main import app
    guest = TestClient(app)
    mid = page['id']
    assert guest.get(f'/api/v1/memorials/{mid}').json()['memories'] == []
    submitted = guest.post(f'/api/v1/memorials/{mid}/memories/public', json={
        'contributor_name': 'Родственник', 'content': 'Вымышленная история для проверки модерации.'})
    assert submitted.status_code == 201, submitted.text
    memory = submitted.json()
    assert memory['status'] == 'pending'
    assert auth_client.get(f'/api/v1/memorials/{mid}/memories').json() == []
    assert auth_client.post(f"/api/v1/memorials/{mid}/memories/{memory['id']}/approve").status_code == 200
    mobile = device_session()
    assert mobile.get(f'/api/v1/memorials/{mid}/memories').json()[0]['contributor_name'] == 'Родственник'
    assert guest.get(f'/api/v1/memorials/{mid}/memories').json() == []


def test_video_and_native_mp4_audio_are_visible_on_other_device(auth_client, tmp_path):
    mobile = device_session()
    page = mobile.post('/api/v1/memorials/', json={'name': 'Проверка видео'}).json()
    mid = page['id']
    video = tmp_path / 'family.mp4'
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=tan:s=160x160:d=0.3',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(video)], check=True, capture_output=True)
    recording = tmp_path / 'voice.mp4'
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=16000:cl=mono',
                    '-t', '0.3', '-c:a', 'aac', str(recording)], check=True, capture_output=True)
    for file, mime, kind in [(video, 'video/mp4', 'video'), (recording, 'audio/mp4', 'audio')]:
        uploaded = mobile.post(f'/api/v1/memorials/{mid}/media/upload',
                               files={'file': (file.name, file.read_bytes(), mime)})
        assert uploaded.status_code == 201, uploaded.text
        media = uploaded.json()
        assert media['media_type'] == kind
        assert media['id'] in [m['id'] for m in auth_client.get(f'/api/v1/memorials/{mid}/media').json()]
        response = auth_client.get(f"/api/v1/media/{media['id']}")
        assert response.status_code == 200
        assert response.content == file.read_bytes()
