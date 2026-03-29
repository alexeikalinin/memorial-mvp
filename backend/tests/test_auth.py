"""
Тесты аутентификации: регистрация, логин, /me, защита эндпоинтов.
"""


def test_register_success(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client, registered_user):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",  # уже занят registered_user
            "username": "anotheruser",
            "full_name": "Another",
            "password": "password123",
        },
    )
    assert resp.status_code == 400
    assert "Email already registered" in resp.json()["detail"]


def test_register_duplicate_username(client, registered_user):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "unique@example.com",
            "username": "testuser",  # уже занят
            "full_name": "Another",
            "password": "password123",
        },
    )
    assert resp.status_code == 400
    assert "Username already taken" in resp.json()["detail"]


def test_register_short_password(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "short",  # меньше 8 символов
        },
    )
    assert resp.status_code == 422


def test_login_success(client, registered_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"


def test_login_wrong_password(client, registered_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "Incorrect" in resp.json()["detail"]


def test_login_unknown_email(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "somepassword"},
    )
    assert resp.status_code == 401


def test_me_with_valid_token(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_me_without_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_fake_token(client):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.fake"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_without_auth(client):
    """Создание мемориала без токена — 401."""
    resp = client.post(
        "/api/v1/memorials/",
        json={"name": "Мемориал без токена"},
    )
    assert resp.status_code == 401


def test_oauth2_token_endpoint(client, registered_user):
    """OAuth2 form-based endpoint /auth/token."""
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
