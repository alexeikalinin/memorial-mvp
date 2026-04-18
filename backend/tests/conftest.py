"""
Общие фикстуры для всех тестов.
"""
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db

# In-memory SQLite с StaticPool — все соединения используют одну БД
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "testpassword123",
}

_TEST_USER_2 = {
    "email": "other@example.com",
    "username": "otheruser",
    "full_name": "Other User",
    "password": "otherpassword123",
}


@pytest.fixture
def db_session():
    """Сессия БД в памяти — создаётся и удаляется для каждого теста."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """TestClient с подменой get_db на in-memory SQLite."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    saved = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    if saved is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = saved


@pytest.fixture(autouse=True)
def _bypass_billing(monkeypatch):
    """Disable billing guards globally in tests — quota/plan checks are not the subject under test."""
    import app.api.memorials as mem_api
    import app.api.ai as ai_api
    noop = lambda *a, **kw: None
    monkeypatch.setattr(mem_api, "check_memorial_limit", noop)
    monkeypatch.setattr(ai_api, "check_chat_quota", noop)
    monkeypatch.setattr(ai_api, "check_animation_quota", noop)
    monkeypatch.setattr(ai_api, "check_tts_access", noop)
    monkeypatch.setattr(ai_api, "check_family_rag_access", noop)


@pytest.fixture
def registered_user(client):
    """Регистрирует пользователя и возвращает его данные."""
    resp = client.post("/api/v1/auth/register", json=_TEST_USER)
    assert resp.status_code == 201, f"Register failed: {resp.json()}"
    return resp.json()


@pytest.fixture
def auth_headers(client, registered_user):
    """Авторизует пользователя и возвращает headers с JWT токеном."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": _TEST_USER["email"], "password": _TEST_USER["password"]},
    )
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client, auth_headers):
    """TestClient с автоматической подстановкой auth заголовков."""
    client.headers.update(auth_headers)
    return client


@pytest.fixture
def second_user_headers(client):
    """Регистрирует второго пользователя и возвращает его headers (для тестов IDOR/доступа)."""
    resp = client.post("/api/v1/auth/register", json=_TEST_USER_2)
    assert resp.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": _TEST_USER_2["email"], "password": _TEST_USER_2["password"]},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def memorial(auth_client):
    """Создаёт мемориал от имени авторизованного пользователя."""
    response = auth_client.post(
        "/api/v1/memorials/",
        json={"name": "Тест Тестович", "description": "Тестовый мемориал", "is_public": False},
    )
    assert response.status_code == 201, f"Create memorial failed: {response.json()}"
    return response.json()


@pytest.fixture
def public_memorial(auth_client):
    """Создаёт публичный мемориал."""
    response = auth_client.post(
        "/api/v1/memorials/",
        json={"name": "Публичный мемориал", "description": "Виден всем", "is_public": True},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def memory_with_date(auth_client, memorial):
    """Создаёт воспоминание с датой события."""
    response = auth_client.post(
        f"/api/v1/memorials/{memorial['id']}/memories",
        json={
            "title": "Ранние годы",
            "content": "В марте 1975 года он окончил школу с отличием.",
            "event_date": "1975-03-15T00:00:00",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_png_bytes():
    """Минимальный валидный PNG 10x10 пикселей для тестов загрузки."""
    from PIL import Image
    img = Image.new("RGB", (10, 10), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
