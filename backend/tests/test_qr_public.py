import pytest
from app.api.memorials import _build_public_memorial_url
from app.config import settings

@pytest.mark.parametrize('base, expected', [
    ('http://localhost:5173', 'http://localhost:5173/m/7#chat'),
    ('https://example.com', 'https://example.com/app/m/7#chat'),
    ('https://example.com/app/', 'https://example.com/app/m/7#chat'),
])
def test_qr_chat_url(monkeypatch, base, expected):
    monkeypatch.setattr(settings, 'PUBLIC_FRONTEND_URL', base)
    assert _build_public_memorial_url(7) == expected


def test_qr_requires_public_and_guest_can_read_after_publish(auth_client, memorial, monkeypatch):
    memorial_id = memorial['id']
    assert auth_client.get(f'/api/v1/memorials/{memorial_id}/qr').status_code == 409
    assert auth_client.patch(f'/api/v1/memorials/{memorial_id}', json={'is_public': True}).status_code == 200
    monkeypatch.setattr('app.auth._get_dev_user', lambda db: None)
    for suffix in ['', '/media', '/memories', '/qr']:
        response = auth_client.get(f'/api/v1/memorials/{memorial_id}{suffix}', headers={'Authorization': ''})
        assert response.status_code == 200
