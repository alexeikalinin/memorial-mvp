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

    # Сохраняем текущий override (может быть установлен другим тестовым модулем)
    saved = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Восстанавливаем
    if saved is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = saved


@pytest.fixture
def memorial(client):
    """Создаёт мемориал и возвращает его JSON."""
    response = client.post(
        "/api/v1/memorials/",
        json={"name": "Тест Тестович", "description": "Тестовый мемориал", "is_public": False},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def memory_with_date(client, memorial):
    """Создаёт воспоминание с датой события."""
    response = client.post(
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
