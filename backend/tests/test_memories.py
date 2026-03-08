"""
Тесты CRUD воспоминаний и поиска по ним.
"""


def test_create_memory(client, memorial):
    mid = memorial["id"]
    response = client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={
            "title": "Детство",
            "content": "Он любил рыбалку и лето.",
            "event_date": "1970-06-01T00:00:00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Детство"
    assert data["content"] == "Он любил рыбалку и лето."
    assert data["event_date"] is not None
    assert data["memorial_id"] == mid


def test_get_memories_no_filter(client, memorial):
    mid = memorial["id"]
    # Создаём два воспоминания
    for i in range(2):
        client.post(
            f"/api/v1/memorials/{mid}/memories",
            json={"title": f"Воспоминание {i}", "content": f"Содержание {i}"},
        )
    response = client.get(f"/api/v1/memorials/{mid}/memories")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_search_memories_by_title(client, memorial):
    mid = memorial["id"]
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Война", "content": "Он воевал на фронте."},
    )
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Мирное время", "content": "После войны он вернулся домой."},
    )

    response = client.get(f"/api/v1/memorials/{mid}/memories?q=Война")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Война"


def test_search_memories_by_content(client, memorial):
    mid = memorial["id"]
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Путешествие", "content": "Он побывал в Париже в 1965 году."},
    )
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Юность", "content": "Учёба и друзья."},
    )

    response = client.get(f"/api/v1/memorials/{mid}/memories?q=Париже")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Париже" in data[0]["content"]


def test_search_memories_empty_result(client, memorial):
    mid = memorial["id"]
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Что-то", "content": "Просто текст."},
    )

    response = client.get(f"/api/v1/memorials/{mid}/memories?q=несуществующеeslovo123")
    assert response.status_code == 200
    assert response.json() == []


def test_update_memory(client, memorial):
    mid = memorial["id"]
    create_resp = client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Старый заголовок", "content": "Старый текст"},
    )
    memory_id = create_resp.json()["id"]

    response = client.patch(
        f"/api/v1/memorials/{mid}/memories/{memory_id}",
        json={"title": "Новый заголовок", "content": "Обновлённый текст"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Новый заголовок"
    assert data["content"] == "Обновлённый текст"


def test_delete_memory(client, memorial):
    mid = memorial["id"]
    create_resp = client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Удаляемое", "content": "Это воспоминание будет удалено."},
    )
    memory_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/memorials/{mid}/memories/{memory_id}")
    assert delete_resp.status_code == 204

    # Убеждаемся, что воспоминание пропало из списка
    list_resp = client.get(f"/api/v1/memorials/{mid}/memories")
    ids = [m["id"] for m in list_resp.json()]
    assert memory_id not in ids
