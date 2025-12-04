"""
Тесты для endpoints мемориалов.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db
from app.models import Memorial

# Тестовая БД в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override для тестовой БД."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def setup_database():
    """Создание и очистка тестовой БД перед каждым тестом."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_create_memorial(setup_database):
    """Тест создания мемориала."""
    response = client.post(
        "/api/v1/memorials/",
        json={
            "name": "Тестовый мемориал",
            "description": "Описание тестового мемориала",
            "is_public": False
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Тестовый мемориал"
    assert data["id"] is not None


def test_get_memorial(setup_database):
    """Тест получения мемориала."""
    # Создаем мемориал
    create_response = client.post(
        "/api/v1/memorials/",
        json={
            "name": "Тестовый мемориал",
            "description": "Описание",
            "is_public": False
        }
    )
    memorial_id = create_response.json()["id"]
    
    # Получаем мемориал
    response = client.get(f"/api/v1/memorials/{memorial_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memorial_id
    assert data["name"] == "Тестовый мемориал"


def test_get_nonexistent_memorial(setup_database):
    """Тест получения несуществующего мемориала."""
    response = client.get("/api/v1/memorials/999")
    assert response.status_code == 404

