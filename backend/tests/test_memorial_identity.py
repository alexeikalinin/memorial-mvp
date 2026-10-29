def test_identity_fields_are_optional_and_roundtrip_without_changing_voice(auth_client):
    response=auth_client.post('/api/v1/memorials/',json={'name':'Synthetic Person','gender':'female','maiden_name':'Birth Surname','voice_gender':'male'})
    assert response.status_code == 201
    data=response.json(); mid=data['id']
    assert data['gender']=='female' and data['maiden_name']=='Birth Surname' and data['voice_gender']=='male'
    tree=auth_client.get(f'/api/v1/family/memorials/{mid}/full-tree').json()
    node=next(n for n in tree['nodes'] if n['memorial_id']==mid)
    assert node['gender']=='female' and node['maiden_name']=='Birth Surname'
    result=auth_client.patch(f'/api/v1/memorials/{mid}',json={'gender':'male','maiden_name':None})
    assert result.status_code==200
    assert result.json()['gender']=='male' and result.json()['maiden_name'] is None
    assert auth_client.patch(f'/api/v1/memorials/{mid}',json={'gender':'invalid'}).status_code==422


def test_birth_surname_search_matches_all_tokens_and_respects_access(client, auth_headers, second_user_headers):
    public=client.post('/api/v1/memorials/',headers=auth_headers,json={'name':'Калинина Светлана','gender':'female','maiden_name':'Бахар','is_public':True}).json()
    private=client.post('/api/v1/memorials/',headers=auth_headers,json={'name':'Калинина Светлана','gender':'female','maiden_name':'Бахар','is_public':False}).json()
    result=client.get('/api/v1/family/search',params={'q':'Светлана Бахар'},headers=second_user_headers)
    assert result.status_code==200
    assert [m['id'] for m in result.json()]==[public['id']]
    assert result.json()[0]['maiden_name']=='Бахар'
    own=client.get('/api/v1/family/search',params={'q':'Бахар Светлана'},headers=auth_headers).json()
    assert {m['id'] for m in own}=={public['id'],private['id']}
    assert not client.get('/api/v1/family/search',params={'q':'Светлана Missing'},headers=auth_headers).json()
    listed=client.get('/api/v1/memorials/',headers=auth_headers).json()
    assert next(m for m in listed if m['id']==public['id'])['maiden_name']=='Бахар'
