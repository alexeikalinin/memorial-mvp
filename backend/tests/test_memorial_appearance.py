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
    assert response.json()['appearance_settings'] == appearance
    assert client.get(path).json()['appearance_settings'] == appearance
    assert auth_client.patch(path, json={'description': 'New'}).json()['appearance_settings'] == appearance
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
