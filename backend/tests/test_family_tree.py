"""
Тесты семейного дерева и связей между мемориалами.
"""


def create_memorial(client, name):
    resp = client.post("/api/v1/memorials/", json={"name": name, "is_public": False})
    assert resp.status_code == 201
    return resp.json()


def test_create_relationship(client):
    m1 = create_memorial(client, "Отец")
    m2 = create_memorial(client, "Сын")

    response = client.post(
        f"/api/v1/family/memorials/{m1['id']}/relationships",
        json={"related_memorial_id": m2["id"], "relationship_type": "child"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["memorial_id"] == m1["id"]
    assert data["related_memorial_id"] == m2["id"]
    assert data["relationship_type"] == "child"
    assert data["related_memorial_name"] == "Сын"


def test_create_duplicate_relationship(client):
    """Повторная связь того же типа возвращает 400."""
    m1 = create_memorial(client, "Дедушка")
    m2 = create_memorial(client, "Внук")

    client.post(
        f"/api/v1/family/memorials/{m1['id']}/relationships",
        json={"related_memorial_id": m2["id"], "relationship_type": "child"},
    )

    response = client.post(
        f"/api/v1/family/memorials/{m1['id']}/relationships",
        json={"related_memorial_id": m2["id"], "relationship_type": "child"},
    )
    assert response.status_code == 400


def test_get_relationships(client):
    m1 = create_memorial(client, "Мать")
    m2 = create_memorial(client, "Дочь")
    client.post(
        f"/api/v1/family/memorials/{m1['id']}/relationships",
        json={"related_memorial_id": m2["id"], "relationship_type": "child"},
    )

    response = client.get(f"/api/v1/family/memorials/{m1['id']}/relationships")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(r["related_memorial_id"] == m2["id"] for r in data)


def test_delete_relationship(client):
    m1 = create_memorial(client, "Брат")
    m2 = create_memorial(client, "Сестра")
    create_resp = client.post(
        f"/api/v1/family/memorials/{m1['id']}/relationships",
        json={"related_memorial_id": m2["id"], "relationship_type": "sibling"},
    )
    rel_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/family/relationships/{rel_id}")
    assert delete_resp.status_code == 204

    # Убеждаемся что связь исчезла
    list_resp = client.get(f"/api/v1/family/memorials/{m1['id']}/relationships")
    ids = [r["id"] for r in list_resp.json()]
    assert rel_id not in ids


def test_get_family_tree(client):
    """Дерево содержит корневой узел с именем мемориала."""
    root = create_memorial(client, "Корень")
    child = create_memorial(client, "Дочерний узел")

    # root -> child (child relationship)
    client.post(
        f"/api/v1/family/memorials/{root['id']}/relationships",
        json={"related_memorial_id": child["id"], "relationship_type": "child"},
    )

    response = client.get(f"/api/v1/family/memorials/{root['id']}/tree")
    assert response.status_code == 200
    data = response.json()
    assert "root" in data
    assert "total_nodes" in data
    assert data["root"]["memorial_id"] == root["id"]
    assert data["root"]["name"] == "Корень"
    # Дочерний узел попадает в children
    children_ids = [c["memorial_id"] for c in data["root"]["children"]]
    assert child["id"] in children_ids
