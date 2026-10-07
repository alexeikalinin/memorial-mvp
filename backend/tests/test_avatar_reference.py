"""Image contract tests: preserve identity pixels, orientation and original files."""
import io
from PIL import Image
import pytest
from app.services.media_service import prepare_avatar_reference
from app.models import Media, MediaType


def encode(image, **kwargs):
    result = io.BytesIO()
    image.save(result, 'PNG', **kwargs)
    return result.getvalue()


def test_reference_preserves_full_frame_and_does_not_upscale():
    source = encode(Image.new('RGB', (300, 150), 'red'))
    result = Image.open(io.BytesIO(prepare_avatar_reference(source)))
    assert result.size == (300, 300)
    assert result.format == 'JPEG' and result.mode == 'RGB'
    assert result.info['icc_profile']
    assert result.getpixel((150, 150))[0] > 240
    assert min(result.getpixel((150, 10))) > 240
    assert Image.open(io.BytesIO(source)).size == (300, 150)


def test_reference_orientation_size_and_metadata():
    image = Image.new('RGB', (2400, 1200), 'blue')
    exif = Image.Exif()
    exif[274] = 6
    exif[315] = 'private metadata'
    result = Image.open(io.BytesIO(prepare_avatar_reference(encode(image, exif=exif))))
    assert result.size == (1024, 1024)
    assert not result.getexif()
    # EXIF rotation makes the content tall, so white margins are left/right.
    assert min(result.getpixel((10, 512))) > 240
    assert result.getpixel((512, 10))[2] > 240


def test_reference_flattens_transparency():
    image = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    result = Image.open(io.BytesIO(prepare_avatar_reference(encode(image))))
    assert min(result.getpixel((50, 50))) > 240


def test_reference_rejects_invalid_input():
    with pytest.raises(Exception):
        prepare_avatar_reference(b'not an image')


@pytest.mark.parametrize('remote', [False, True])
def test_reference_endpoint_local_and_storage(client, memorial, db_session, tmp_path, monkeypatch, remote):
    import app.api.media as api
    source = encode(Image.new('RGB', (160, 80), 'green'))
    original = tmp_path / 'original.png'
    original.write_bytes(source)
    media = Media(memorial_id=memorial['id'], file_path='memorials/portrait.png' if remote else str(original),
                  file_name='portrait.png', media_type=MediaType.PHOTO)
    db_session.add(media)
    db_session.commit()
    monkeypatch.setattr(api.settings, 'USE_S3', remote)
    class Storage:
        def download_fileobj(self, bucket, key, output):
            assert key == 'memorials/portrait.png'
            output.write(source)
    monkeypatch.setattr(api, 'get_s3_client', lambda: Storage())
    response = client.get(f'/api/v1/media/avatar/{media.id}.jpg')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/jpeg'
    assert Image.open(io.BytesIO(response.content)).size == (160, 160)
    assert original.read_bytes() == source
