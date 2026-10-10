"""Memorial decoration persistence, validation and access."""
import pytest


def test_appearance_saved_and_public(auth_client, client):
    created = auth_client.post('/api/v1/memorials/', json={
        'name': 'Appearance demo', 'is_public': True,
    }).json()
    path = f"/api/v1/memorials/{created['id']}"
    appearance = {'font': 'serif', 'font_size': 28, 'layout': None, 'layout_mobile': None, 'quote': 'Помним тебя', 'flowers': 'white_carnations', 'candle': 'lampada'}
    response = auth_client.patch(path, json={'appearance_settings': appearance})
    assert response.status_code == 200
    assert all(response.json()['appearance_settings'][key] == value for key, value in appearance.items())
    assert all(client.get(path).json()['appearance_settings'][key] == value for key, value in appearance.items())
    assert all(auth_client.patch(path, json={'description': 'New'}).json()['appearance_settings'][key] == value for key, value in appearance.items())
    assert auth_client.patch(path, json={'appearance_settings': None}).json()['appearance_settings'] is None


@pytest.mark.parametrize('appearance', [
    {'quote': 'x' * 161}, {'flowers': 'arbitrary-url'},
    {'candle': 'unknown'}, {'html': '<script>'},
])
def test_appearance_validation(auth_client, memorial, appearance):
    response = auth_client.patch(f"/api/v1/memorials/{memorial['id']}",
                                 json={'appearance_settings': appearance})
    assert response.status_code == 422


def test_appearance_requires_edit_access(client, second_user_headers, memorial):
    path = f"/api/v1/memorials/{memorial['id']}"
    response = client.patch(path, headers=second_user_headers,
                            json={'appearance_settings': {'quote': 'Other user'}})
    assert response.status_code in (403, 404)


def test_name_date_style_is_not_content_edit(auth_client, memorial):
    path = f"/api/v1/memorials/{memorial['id']}"
    before = auth_client.get(path).json()
    styles = {'font_name':'playfair', 'font_size_name':60, 'font_dates':'pt_serif', 'font_size_dates':18,
              'flower_type':'lilies', 'flower_color':'white', 'candle':'beeswax',
              'layout':{'name':{'x':.4,'y':.3,'scale':1},'dates':{'x':.4,'y':.5,'scale':.8}}}
    response = auth_client.patch(path, json={'appearance_settings':styles})
    assert response.status_code == 200
    after = auth_client.get(path).json()
    assert (after['name'],after['birth_date'],after['death_date']) == (before['name'],before['birth_date'],before['death_date'])
    assert after['appearance_settings']['flower_type'] == 'lilies'
    assert after['appearance_settings']['layout']['name']['x'] == .4
    for bad in [{'name':'Changed'}, {'font_name':'unknown'}, {'font_size_name':73},
                {'font_size_dates':9}, {'flower_type':'unknown'}, {'flower_color':'neon'}]:
        assert auth_client.patch(path, json={'appearance_settings':bad}).status_code == 422
