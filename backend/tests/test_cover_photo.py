"""
Тесты управления фото обложки мемориала.
"""
import io


def upload_photo(client, memorial_id, png_bytes):
    """Вспомогательная функция: загружает PNG и возвращает media JSON."""
    response = client.post(
        f"/api/v1/memorials/{memorial_id}/media/upload",
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_set_cover_photo(client, memorial, test_png_bytes):
    mid = memorial["id"]
    media = upload_photo(client, mid, test_png_bytes)

    response = client.patch(
        f"/api/v1/memorials/{mid}/cover",
        json={"media_id": media["id"]},
    )
    assert response.status_code == 200
    assert response.json()["cover_photo_id"] == media["id"]


def test_unset_cover_photo(client, memorial, test_png_bytes):
    mid = memorial["id"]
    media = upload_photo(client, mid, test_png_bytes)

    # Устанавливаем
    client.patch(f"/api/v1/memorials/{mid}/cover", json={"media_id": media["id"]})

    # Снимаем
    response = client.patch(f"/api/v1/memorials/{mid}/cover", json={"media_id": None})
    assert response.status_code == 200
    assert response.json()["cover_photo_id"] is None


def test_set_cover_wrong_memorial(client, memorial, test_png_bytes):
    """Нельзя назначить обложкой медиа из другого мемориала."""
    mid = memorial["id"]
    media = upload_photo(client, mid, test_png_bytes)

    # Создаём другой мемориал
    other_resp = client.post(
        "/api/v1/memorials/",
        json={"name": "Другой мемориал", "is_public": False},
    )
    other_id = other_resp.json()["id"]

    # Пытаемся назначить медиа первого мемориала как обложку второго
    response = client.patch(
        f"/api/v1/memorials/{other_id}/cover",
        json={"media_id": media["id"]},
    )
    assert response.status_code == 404


def test_cover_photo_id_in_list(client, memorial, test_png_bytes):
    """cover_photo_id присутствует в ответе списка мемориалов."""
    mid = memorial["id"]
    media = upload_photo(client, mid, test_png_bytes)
    client.patch(f"/api/v1/memorials/{mid}/cover", json={"media_id": media["id"]})

    list_resp = client.get("/api/v1/memorials/")
    assert list_resp.status_code == 200
    item = next(m for m in list_resp.json() if m["id"] == mid)
    assert item["cover_photo_id"] == media["id"]


def test_cover_photo_id_in_detail(client, memorial, test_png_bytes):
    """cover_photo_id присутствует в детальном ответе мемориала."""
    mid = memorial["id"]
    media = upload_photo(client, mid, test_png_bytes)
    client.patch(f"/api/v1/memorials/{mid}/cover", json={"media_id": media["id"]})

    detail_resp = client.get(f"/api/v1/memorials/{mid}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["cover_photo_id"] == media["id"]
