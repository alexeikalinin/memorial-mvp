"""
Тесты инвайт-ссылок: создание, валидация, вклад без авторизации, отзыв.
"""
from datetime import datetime, timedelta


def test_create_invite(auth_client, memorial):
    """Владелец может создать инвайт."""
    resp = auth_client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Для Ивановых",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "permissions": {"add_memories": True, "chat": True, "view_media": True},
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["label"] == "Для Ивановых"
    return data["token"]


def test_validate_invite_token(auth_client, client, memorial):
    """Валидация токена возвращает название мемориала."""
    create_resp = auth_client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Test",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "permissions": {"add_memories": True, "chat": True, "view_media": True},
        },
    )
    token = create_resp.json()["token"]

    # Валидируем без авторизации
    resp = client.get(f"/api/v1/invites/validate/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["memorial_name"] == memorial["name"]


def test_add_memory_via_invite(auth_client, client, memorial):
    """Добавление воспоминания через инвайт-токен (без авторизации)."""
    create_resp = auth_client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Семья",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "permissions": {"add_memories": True, "chat": True, "view_media": True},
        },
    )
    token = create_resp.json()["token"]

    mem_resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/memories?invite_token={token}",
        json={"title": "Вклад гостя", "content": "Он был добрым человеком."},
    )
    assert mem_resp.status_code == 201
    assert mem_resp.json()["title"] == "Вклад гостя"


def test_expired_invite_token(auth_client, client, memorial):
    """Истёкший инвайт не работает."""
    create_resp = auth_client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Устаревший",
            "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "permissions": {"add_memories": True, "chat": True, "view_media": True},
        },
    )
    token = create_resp.json()["token"]

    resp = client.get(f"/api/v1/invites/validate/{token}")
    assert resp.status_code in (400, 404, 410)


def test_invalid_invite_token(client):
    """Несуществующий токен возвращает 404."""
    resp = client.get("/api/v1/invites/validate/totally-fake-token-xyz")
    assert resp.status_code == 404


def test_list_invites(auth_client, memorial):
    """Список инвайтов мемориала."""
    auth_client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Первый",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "permissions": {"add_memories": True, "chat": True, "view_media": True},
        },
    )
    auth_client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Второй",
            "expires_at": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "permissions": {"add_memories": False, "chat": True, "view_media": True},
        },
    )

    resp = auth_client.get(f"/api/v1/invites/memorials/{memorial['id']}/list")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_revoke_invite(auth_client, client, memorial):
    """Отзыв инвайта делает его невалидным."""
    create_resp = auth_client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Отзываемый",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "permissions": {"add_memories": True, "chat": True, "view_media": True},
        },
    )
    token = create_resp.json()["token"]

    # Отзываем
    del_resp = auth_client.delete(f"/api/v1/invites/{token}")
    assert del_resp.status_code == 204

    # Токен больше не работает
    resp = client.get(f"/api/v1/invites/validate/{token}")
    assert resp.status_code == 404


def test_create_invite_without_auth(client, memorial, monkeypatch):
    """Создать инвайт без авторизации — 401."""
    monkeypatch.setattr("app.auth._get_dev_user", lambda db: None)
    # auth_client modifies client.headers in-place; clear Authorization for anonymous request
    resp = client.post(
        f"/api/v1/invites/memorials/{memorial['id']}/create",
        json={
            "label": "Нелегальный",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "permissions": {"add_memories": True, "chat": True, "view_media": True},
        },
        headers={"Authorization": ""},
    )
    assert resp.status_code == 401
