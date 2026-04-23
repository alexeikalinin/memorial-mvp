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


def test_reject_access_request(auth_client, memorial, client, second_user_headers):
    """Отклонение заявки: статус 204, пользователь доступа не получает."""
    req_resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "viewer"},
        headers=second_user_headers,
    )
    assert req_resp.status_code == 201
    req_id = req_resp.json()["id"]

    reject_resp = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access/requests/{req_id}/reject"
    )
    assert reject_resp.status_code == 204

    # Доступ по-прежнему закрыт
    resp = client.get(
        f"/api/v1/memorials/{memorial['id']}",
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_re_request_after_rejection(auth_client, memorial, client, second_user_headers):
    """После reject можно подать заявку снова — upsert сбрасывает в PENDING."""
    req_resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "viewer"},
        headers=second_user_headers,
    )
    req_id = req_resp.json()["id"]

    # Отклоняем
    auth_client.post(f"/api/v1/memorials/{memorial['id']}/access/requests/{req_id}/reject")

    # Подаём снова
    re_req = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "editor", "message": "Пожалуйста, разрешите!"},
        headers=second_user_headers,
    )
    assert re_req.status_code == 201
    assert re_req.json()["status"] == "pending"
    assert re_req.json()["requested_role"] == "editor"


def test_duplicate_request_upsert(auth_client, memorial, client, second_user_headers):
    """Повторный запрос от того же пользователя — upsert, не дублирование."""
    client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "viewer"},
        headers=second_user_headers,
    )
    # Второй запрос — должен обновить, а не создать новую запись
    second = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "editor"},
        headers=second_user_headers,
    )
    assert second.status_code == 201
    assert second.json()["requested_role"] == "editor"

    # В списке заявок — только одна
    requests_list = auth_client.get(f"/api/v1/memorials/{memorial['id']}/access/requests")
    pending = [r for r in requests_list.json() if r["user_email"] == "other@example.com"]
    assert len(pending) == 1


def test_request_when_already_have_access(auth_client, memorial, client, second_user_headers):
    """Пользователь с уже выданным доступом не может подавать заявку → 400."""
    # Выдаём доступ
    auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "viewer"},
    )
    # Пытаемся запросить доступ, хотя уже есть
    resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "editor"},
        headers=second_user_headers,
    )
    assert resp.status_code == 400


def test_non_owner_cannot_list_access(client, auth_client, memorial, second_user_headers):
    """Не-owner не может просмотреть список доступа."""
    # Выдаём viewer-доступ второму
    auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "viewer"},
    )
    resp = client.get(
        f"/api/v1/memorials/{memorial['id']}/access",
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_non_owner_cannot_see_access_requests(client, auth_client, memorial, second_user_headers):
    """Viewer не может просматривать заявки на доступ."""
    auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access",
        json={"email": "other@example.com", "role": "viewer"},
    )
    resp = client.get(
        f"/api/v1/memorials/{memorial['id']}/access/requests",
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_cannot_revoke_only_owner(auth_client, memorial):
    """Нельзя удалить единственного владельца мемориала."""
    # Получаем id первого пользователя через список доступа
    access_list = auth_client.get(f"/api/v1/memorials/{memorial['id']}/access")
    owner_entry = next(e for e in access_list.json() if e["role"] == "owner")
    owner_user_id = owner_entry["user_id"]

    resp = auth_client.delete(
        f"/api/v1/memorials/{memorial['id']}/access/{owner_user_id}"
    )
    assert resp.status_code == 400


def test_approve_already_approved_request(auth_client, memorial, client, second_user_headers):
    """Повторное одобрение уже одобренной заявки → 400."""
    req_resp = client.post(
        f"/api/v1/memorials/{memorial['id']}/access/request",
        json={"requested_role": "viewer"},
        headers=second_user_headers,
    )
    req_id = req_resp.json()["id"]

    auth_client.post(f"/api/v1/memorials/{memorial['id']}/access/requests/{req_id}/approve")

    second_approve = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/access/requests/{req_id}/approve"
    )
    assert second_approve.status_code == 400
