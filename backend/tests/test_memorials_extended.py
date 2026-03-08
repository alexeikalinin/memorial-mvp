"""
Расширенный CRUD для мемориалов: list, update, delete.
"""


def test_list_memorials_empty(client):
    response = client.get("/api/v1/memorials/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_memorials_with_data(client, memorial):
    response = client.get("/api/v1/memorials/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["id"] == memorial["id"]
    assert item["name"] == memorial["name"]
    assert "memories_count" in item
    assert "media_count" in item
    assert "cover_photo_id" in item


def test_update_memorial(client, memorial):
    mid = memorial["id"]
    response = client.patch(
        f"/api/v1/memorials/{mid}",
        json={"name": "Обновлённое имя", "description": "Новое описание"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Обновлённое имя"
    assert data["description"] == "Новое описание"


def test_delete_memorial(client, memorial):
    mid = memorial["id"]

    delete_response = client.delete(f"/api/v1/memorials/{mid}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/memorials/{mid}")
    assert get_response.status_code == 404
