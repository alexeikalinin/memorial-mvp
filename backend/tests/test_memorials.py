"""
Тесты для endpoints мемориалов.
"""


def test_create_memorial(auth_client):
    """Тест создания мемориала."""
    response = auth_client.post(
        "/api/v1/memorials/",
        json={
            "name": "Тестовый мемориал",
            "description": "Описание тестового мемориала",
            "is_public": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Тестовый мемориал"
    assert data["id"] is not None


def test_get_memorial(auth_client):
    """Тест получения мемориала."""
    create_response = auth_client.post(
        "/api/v1/memorials/",
        json={"name": "Тестовый мемориал", "description": "Описание", "is_public": False},
    )
    assert create_response.status_code == 201
    memorial_id = create_response.json()["id"]

    response = auth_client.get(f"/api/v1/memorials/{memorial_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memorial_id
    assert data["name"] == "Тестовый мемориал"


def test_get_nonexistent_memorial(client):
    """Тест получения несуществующего мемориала."""
    response = client.get("/api/v1/memorials/999")
    assert response.status_code == 404
