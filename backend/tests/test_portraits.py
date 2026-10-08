import io
from PIL import Image
from app.models import Media, MediaType


def photo(db_session, memorial_id, tmp_path, name='photo.png'):
    # Two people represented by distinguishable halves; crop must select one.
    image = Image.new('RGB', (400, 200), 'red')
    image.paste(Image.new('RGB', (200, 200), 'blue'), (200, 0))
    path = tmp_path / name
    image.save(path)
    media = Media(memorial_id=memorial_id, file_path=str(path), file_name=name, media_type=MediaType.PHOTO)
    db_session.add(media); db_session.commit()
    return media


CROP = {'x': .5, 'y': 0, 'width': .5, 'height': 1, 'rotation': 0}


def test_portraits_crop_follow_independence_and_reset(auth_client, memorial, db_session, tmp_path):
    p = photo(db_session, memorial['id'], tmp_path)
    endpoint = f"/api/v1/memorials/{memorial['id']}/portraits"
    res = auth_client.patch(endpoint+'/cover', json={'media_id': p.id, 'crop': CROP})
    assert res.status_code == 200
    assert res.json()['portrait_settings']['cover']['crop'] == CROP
    for kind in ('cover', 'avatar'):
        response = auth_client.get(f"/api/v1/media/portrait/{memorial['id']}/{kind}.jpg")
        assert response.status_code == 200
        image = Image.open(io.BytesIO(response.content))
        assert image.size == (200, 200)
        assert image.getpixel((100,100))[2] > 240
    red = {**CROP, 'x': 0}
    assert auth_client.patch(endpoint+'/avatar', json={'media_id': p.id, 'crop': red}).status_code == 200
    second = photo(db_session, memorial['id'], tmp_path, 'another.png')
    assert auth_client.patch(endpoint+'/cover', json={'media_id': second.id, 'crop': CROP}).status_code == 200
    image = Image.open(io.BytesIO(auth_client.get(f"/api/v1/media/portrait/{memorial['id']}/avatar.jpg").content))
    assert image.getpixel((100,100))[0] > 240  # Independent crop survived the header change.
    assert auth_client.patch(endpoint+'/avatar', json={'media_id': None}).status_code == 200
    image = Image.open(io.BytesIO(auth_client.get(f"/api/v1/media/portrait/{memorial['id']}/avatar.jpg").content))
    assert image.getpixel((100,100))[2] > 240
    assert Image.open(p.file_path).size == (400,200)  # Never rewrite originals.


def test_portrait_invalid_crop_type_and_cross_memorial(auth_client, memorial, db_session, tmp_path):
    p = photo(db_session, memorial['id'], tmp_path)
    endpoint = f"/api/v1/memorials/{memorial['id']}/portraits/cover"
    assert auth_client.patch(endpoint, json={'media_id': p.id,'crop': {**CROP,'x': .9}}).status_code == 422
    assert auth_client.patch(endpoint, json={'media_id': p.id,'crop': {**CROP,'rotation': 45}}).status_code == 422
    assert auth_client.patch(endpoint, json={'media_id': None,'crop': CROP}).status_code == 422
    another = auth_client.post('/api/v1/memorials/',json={'name':'Other memorial'}).json()
    assert auth_client.patch(f"/api/v1/memorials/{another['id']}/portraits/cover",json={'media_id':p.id}).status_code == 404
    audio = Media(memorial_id=memorial['id'], file_path='fake.mp3', file_name='fake.mp3', media_type=MediaType.AUDIO)
    db_session.add(audio); db_session.commit()
    assert auth_client.patch(endpoint,json={'media_id':audio.id}).status_code == 400


def test_portrait_edit_needs_access_and_delete_clears_references(auth_client, client, second_user_headers, memorial, db_session, tmp_path, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "DEBUG", False)
    p = photo(db_session, memorial['id'], tmp_path)
    endpoint = f"/api/v1/memorials/{memorial['id']}/portraits"
    assert client.patch(endpoint+'/cover',json={'media_id':p.id},headers={'Authorization':''}).status_code == 401
    assert client.patch(endpoint+'/cover',json={'media_id':p.id},headers=second_user_headers).status_code == 403
    for kind in ('cover','avatar'):
        assert auth_client.patch(endpoint+'/'+kind,json={'media_id':p.id,'crop':CROP}).status_code == 200
    assert auth_client.delete(f"/api/v1/memorials/{memorial['id']}/media/{p.id}").status_code == 204
    res=auth_client.get(f"/api/v1/memorials/{memorial['id']}").json()
    assert res['cover_photo_id'] is None
    assert not res['portrait_settings'].get('avatar')


def test_family_tree_uses_selected_avatar_and_crop(auth_client, memorial, db_session, tmp_path):
    first = photo(db_session, memorial['id'], tmp_path)
    second = photo(db_session, memorial['id'], tmp_path, 'avatar.png')
    endpoint = f"/api/v1/memorials/{memorial['id']}/portraits"
    assert auth_client.patch(endpoint+'/cover', json={'media_id': first.id, 'crop': CROP}).status_code == 200
    assert auth_client.patch(endpoint+'/avatar', json={'media_id': second.id, 'crop': CROP}).status_code == 200
    response = auth_client.get(f"/api/v1/family/memorials/{memorial['id']}/full-tree")
    assert response.status_code == 200
    node = next(n for n in response.json()['nodes'] if n['memorial_id'] == memorial['id'])
    assert node['cover_photo_id'] == first.id
    assert node['avatar_photo_id'] == second.id
    assert node['portrait_settings']['avatar']['crop'] == CROP
    assert auth_client.patch(endpoint+'/avatar', json={'media_id': None}).status_code == 200
    node = auth_client.get(f"/api/v1/family/memorials/{memorial['id']}/full-tree").json()['nodes'][0]
    assert node['avatar_photo_id'] == first.id
