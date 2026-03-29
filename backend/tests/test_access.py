"""
Тесты управления доступом: IDOR-защита, grant/revoke, access requests.
"""
import pytest


# ─── IDOR / Изоляция ─────────────────────────────────────────────────────────

def test_cannot_delete_others_memorial(client, auth_client, memorial, second_user_headers):
    """Второй пользователь не может удалить мемориал первого."""
    resp = client.delete(
        f"/api/v1/memorials/{memorial['id']}",
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_cannot_update_others_memorial(client, auth_client, memorial, second_user_headers):
    """Второй пользователь не может редактировать мемориал первого."""
    resp = client.patch(
        f"/api/v1/memorials/{memorial['id']}",
        json={"name": "Взломанное имя"},
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_cannot_add_media_to_others_memorial(client, memorial, second_user_headers, test_png_bytes):
    """Второй пользователь не может загружать медиа в чужой мемориал."""
    resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/media/upload",
        files={"file": ("test.png", test_png_bytes, "image/png")},
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_memorial_list_only_own(client, auth_client, second_user_headers):
    """Список мемориалов возвращает только свои."""
    # Создаём мемориал от первого пользователя
    auth_client.post("/api/v1/memorials/", json={"name": "Мой мемориал"})
    # Получаем список от второго пользователя
    resp = client.get("/api/v1/memorials/", headers=second_user_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_private_memorial_hidden_from_anonymous(client, memorial, monkeypatch):
    """Приватный мемориал недоступен без авторизации."""
    monkeypatch.setattr("app.auth._get_dev_user", lambda db: None)
    # auth_client modifies client.headers in-place; clear Authorization for anonymous request
    resp = client.get(
        f"/api/v1/memorials/{memorial['id']}",
        headers={"Authorization": ""},
    )
    assert resp.status_code in (401, 403)


# ─── Grant / Revoke ────────────────────────────────────────────────────────────

def test_owner_can_grant_access(client, auth_client, memorial, second_user_headers):
    """Владелец может выдать доступ другому пользователю."""
    resp = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "viewer"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "viewer"
    assert data["user_email"] == "other@example.com"


def test_granted_viewer_can_read(client, auth_client, memorial, second_user_headers):
    """Пользователь с ролью viewer может читать мемориал."""
    # Выдаём доступ
    auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "viewer"},
    )
    # Второй читает
    resp = client.get(
        f"/api/v1/memorials/{memorial['id']}",
        headers=second_user_headers,
    )
    assert resp.status_code == 200


def test_viewer_cannot_add_memory(client, auth_client, memorial, second_user_headers):
    """Viewer не может добавлять воспоминания."""
    auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "viewer"},
    )
    resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/memories",
        json={"title": "Нелегальное", "content": "Попытка viewer"},
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_editor_can_add_memory(client, auth_client, memorial, second_user_headers):
    """Editor может добавлять воспоминания."""
    auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "editor"},
    )
    resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/memories",
        json={"title": "Легальное", "content": "Editor может"},
        headers=second_user_headers,
    )
    assert resp.status_code == 201


def test_update_access_role(client, auth_client, memorial, second_user_headers):
    """Владелец может сменить роль пользователя."""
    grant_resp = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "viewer"},
    )
    assert grant_resp.status_code == 201, grant_resp.json()
    target_user_id = grant_resp.json()["user_id"]

    resp = auth_client.patch(
        f"/api/v1/memorials/{memorial['id']}/access/{target_user_id}",
        json={"role": "editor"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "editor"


def test_revoke_access(client, auth_client, memorial, second_user_headers):
    """Владелец может отозвать доступ."""
    grant_resp = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "editor"},
    )
    access_id = grant_resp.json()["id"]

    revoke_resp = auth_client.delete(
        f"/api/v1/memorials/{memorial['id']}/access/{access_id}"
    )
    assert revoke_resp.status_code == 204

    # После отзыва — доступ закрыт
    resp = client.get(
        f"/api/v1/memorials/{memorial['id']}",
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_cannot_grant_owner_role(auth_client, memorial):
    """Нельзя выдать роль owner через API."""
    resp = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "owner"},
    )
    assert resp.status_code in (400, 422)


# ─── Access Requests ──────────────────────────────────────────────────────────

def test_request_access_to_private_memorial(client, auth_client, memorial, second_user_headers):
    """Авторизованный пользователь может запросить доступ к приватному мемориалу."""
    resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "viewer"},
        headers=second_user_headers,
    )
    assert resp.status_code == 201


def test_owner_sees_access_requests(auth_client, memorial, client, second_user_headers):
    """Владелец видит список заявок."""
    client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "viewer"},
        headers=second_user_headers,
    )
    resp = auth_client.get(f"/api/v1/memorials/{memorial['id']}/access/requests")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_approve_access_request(auth_client, memorial, client, second_user_headers):
    """Одобрение заявки даёт пользователю доступ."""
    req_resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "viewer"},
        headers=second_user_headers,
    )
    req_id = req_resp.json()["id"]

    approve_resp = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access/requests/{req_id}/approve"
    )
    assert approve_resp.status_code == 200

    # Теперь второй пользователь может читать
    resp = client.get(
        f"/api/v1/memorials/{memorial['id']}",
        headers=second_user_headers,
    )
    assert resp.status_code == 200
