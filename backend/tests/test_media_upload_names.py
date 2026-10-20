"""User filenames must not become object storage keys."""
from pathlib import Path

import pytest


@pytest.mark.parametrize("filename", ["ма.png", "мама ❤️.png", "portrait.png"])
def test_upload_preserves_display_name_with_safe_storage_key(
    client, memorial, test_png_bytes, tmp_path, monkeypatch, filename
):
    import app.api.memorials as api

    monkeypatch.setattr(api.settings, "USE_S3", True)
    monkeypatch.setattr(api.settings, "SUPABASE_URL", "https://storage.example")
    monkeypatch.setattr(api, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(api, "THUMBNAILS_DIR", tmp_path)
    uploaded = {}

    def upload(path, key, content_type):
        assert key.isascii()
        assert Path(key).name != filename
        uploaded[key] = Path(path).read_bytes()
        return True

    monkeypatch.setattr(api, "upload_file_to_s3", upload)
    response = client.post(
        f"/api/v1/memorials/{memorial['id']}/media/upload",
        files={"file": (filename, test_png_bytes, "image/png")},
    )
    assert response.status_code == 201, response.text
    media = response.json()
    assert media["file_name"] == filename
    assert uploaded[media["file_path"]] == test_png_bytes
    assert media["file_url"].endswith(media["file_path"])
    if media["thumbnail_path"]:
        assert media["thumbnail_path"] in uploaded
