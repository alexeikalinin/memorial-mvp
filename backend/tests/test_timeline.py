"""
Тесты хронологии жизни (GET /memorials/{id}/timeline).
"""


def test_timeline_undated_only(client, memorial):
    """Воспоминание без даты попадает в таймлайн (секция «без даты»)."""
    mid = memorial["id"]
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Без даты", "content": "Просто текст."},
    )

    response = client.get(f"/api/v1/memorials/{mid}/timeline")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Без даты"
    assert data[0]["event_date"] is None
    assert data[0]["date_label"] == "Без даты"


def test_timeline_with_dates(client, memorial):
    """Воспоминания с датами возвращаются отсортированными ASC."""
    mid = memorial["id"]
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Позже", "content": "Событие 1990 года.", "event_date": "1990-06-02T00:00:00"},
    )
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Раньше", "content": "Событие 1975 года.", "event_date": "1975-03-15T00:00:00"},
    )

    response = client.get(f"/api/v1/memorials/{mid}/timeline")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["year"] == 1975
    assert data[1]["year"] == 1990


def test_timeline_dated_then_undated(client, memorial):
    """Сначала события с датой, затем без даты."""
    mid = memorial["id"]
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "С датой", "content": "1980 год.", "event_date": "1980-01-01T00:00:00"},
    )
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Без даты", "content": "Когда-то давно."},
    )

    response = client.get(f"/api/v1/memorials/{mid}/timeline")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "С датой"
    assert data[1]["title"] == "Без даты"
    assert data[1]["event_date"] is None


def test_timeline_item_fields(client, memorial):
    """Каждый элемент таймлайна содержит необходимые поля."""
    mid = memorial["id"]
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Юность", "content": "Учёба.", "event_date": "1965-09-01T00:00:00"},
    )

    response = client.get(f"/api/v1/memorials/{mid}/timeline")
    assert response.status_code == 200
    item = response.json()[0]
    assert "id" in item
    assert "year" in item
    assert "date_label" in item
    assert "content" in item
    assert item["year"] == 1965


def test_timeline_date_label_format(client, memorial):
    """date_label формируется как 'Месяц Год' на русском."""
    mid = memorial["id"]
    # Март = месяц 3
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Март", "content": "Весна.", "event_date": "1975-03-15T00:00:00"},
    )
    # Июнь = месяц 6
    client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Июнь", "content": "Лето.", "event_date": "1990-06-02T00:00:00"},
    )

    response = client.get(f"/api/v1/memorials/{mid}/timeline")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["date_label"] == "Март 1975"
    assert data[1]["date_label"] == "Июнь 1990"
