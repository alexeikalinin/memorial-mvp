import io
import json
from zipfile import ZipFile
from app.models import Memorial, Memory, User


def test_archive_requires_login(client):
    assert client.get('/api/v1/account/export').status_code == 401


def test_archive_is_owned_portable_and_has_no_secrets(auth_client, memorial, db_session):
    other = User(email='other@example.com', username='other', hashed_password='private-password')
    db_session.add(other); db_session.flush()
    hidden = Memorial(name='OTHER PRIVATE PERSON', owner_id=other.id, is_public=False)
    db_session.add(hidden); db_session.flush()
    db_session.add(Memory(memorial_id=hidden.id, content='OTHER PRIVATE MEMORY'))
    db_session.add(Memory(memorial_id=memorial['id'], content='OWN MEMORY'))
    db_session.commit()
    response = auth_client.get('/api/v1/account/export')
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'no-store'
    with ZipFile(io.BytesIO(response.content)) as archive:
        payload = archive.read('data.json').decode()
        assert 'OWN MEMORY' in payload
        assert 'OTHER PRIVATE' not in payload
        data = json.loads(payload)
        assert all('hashed_password' not in u and 'verification_token' not in u for u in data['users'])


def test_archive_includes_original_cloud_file_and_rejects_incomplete_export(auth_client, memorial, db_session, monkeypatch):
    from app.models import Media, MediaType
    from app.config import settings
    from app.services import s3_service
    from unittest.mock import MagicMock
    media = Media(memorial_id=memorial['id'], file_path='test/missing.jpg', file_name='photo.jpg', media_type=MediaType.PHOTO)
    db_session.add(media); db_session.commit()
    monkeypatch.setattr(settings, 'USE_S3', True)
    storage = MagicMock()
    storage.download_fileobj.side_effect = lambda bucket, key, output: output.write(b'original-bytes')
    monkeypatch.setattr(s3_service, 'get_s3_client', lambda: storage)
    response = auth_client.get('/api/v1/account/export')
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.read(f'files/{memorial["id"]}/{media.id}_photo.jpg') == b'original-bytes'
    storage.download_fileobj.side_effect = RuntimeError('unavailable')
    assert auth_client.get('/api/v1/account/export').status_code == 503


def test_export_includes_current_browser_history_only_for_owned_memorials(auth_client, memorial):
    manifest = auth_client.get('/api/v1/account/export/manifest')
    assert manifest.status_code == 200 and manifest.json()['memorial_ids'] == [memorial['id']]
    response = auth_client.post('/api/v1/account/export', json={'chats': {
        str(memorial['id']): [{'role': 'user', 'text': 'My old question'}],
        '9999999': [{'role': 'user', 'text': 'Someone else'}],
    }})
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as archive:
        chats = archive.read('browser-chat-history.json').decode()
        assert 'My old question' in chats and 'Someone else' not in chats
