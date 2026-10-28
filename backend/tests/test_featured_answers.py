from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from app.models import AvatarAnswerCache, FeaturedAvatarAnswer, Memorial, Memory, User, MemorialInvite, GuestChatUsage
from app.schemas import AvatarChatRequest, AvatarChatResponse
from app.services.answer_cache import key_for, save_response


def seed(db, memorial, question='Question'):
    m = db.get(Memorial, memorial['id'])
    owner = db.get(User, m.owner_id)
    memories = db.query(Memory).filter_by(memorial_id=m.id, status='approved').all()
    if not memories:
        db.add(Memory(memorial_id=m.id, content='Approved fact', status='approved')); db.commit()
        memories = db.query(Memory).filter_by(memorial_id=m.id).all()
    req = AvatarChatRequest(memorial_id=m.id, question=question)
    save_response(db,key_for(req,m,memories,owner),req,m,owner,AvatarChatResponse(answer='Saved fact',sources=['Family source']),[f'memory_{memories[0].id}'])
    return m, db.query(AvatarAnswerCache).filter_by(question=question).one(), memories[0]


def publish(client,row,**extra):
    return client.put(f'/api/v1/featured-answers/saved/{row.id}',json={'publish_to_guests':True,**extra})


def test_explicit_selection_text_audio_no_ai_and_guest_quota(auth_client,client,memorial,db_session,monkeypatch,tmp_path):
    from app.api import media,ai
    import app.services.ai_tasks as tasks
    monkeypatch.setattr(media,'UPLOAD_DIR',tmp_path)
    (tmp_path/'audio').mkdir();(tmp_path/'audio'/'saved.mp3').write_bytes(b'mp3')
    m,row,_=seed(db_session,memorial);m.is_public=True
    row.audio_variants={'accepted':{'filename':'saved.mp3'},'pending:take':{'filename':'saved.mp3'}};db_session.commit()
    url=f'/api/v1/featured-answers/memorials/{m.id}/guest'
    assert client.get(url,headers={'Authorization':''}).json()==[]
    assert publish(auth_client,row,audio_variant='pending:take').status_code==422
    assert publish(auth_client,row,audio_variant='accepted').status_code==200
    items=client.get(url,headers={'Authorization':''}).json()
    assert items[0]['answer']=='Saved fact' and items[0]['audio_url']
    assert 'sources' not in items[0] and 'cache_id' not in items[0]
    assert client.get(items[0]['audio_url']).content==b'mp3'
    generator=AsyncMock(side_effect=AssertionError('No LLM/TTS allowed'))
    monkeypatch.setattr(ai,'generate_rag_response',generator);monkeypatch.setattr(tasks,'generate_speech',generator)
    guest='guest-identity-123456789'
    for i in range(5):
        r=client.post(f'/api/v1/ai/avatar/chat?guest_id={guest}',headers={'Authorization':''},json={'memorial_id':m.id,'question':' QUESTION ','include_audio':True})
        assert r.status_code==200,r.text
        assert r.json()['answer']=='Saved fact' and r.json()['audio_url']
    assert client.post(f'/api/v1/ai/avatar/chat?guest_id={guest}',headers={'Authorization':''},json={'memorial_id':m.id,'question':'Question'}).status_code==401
    assert len(client.get(url).json())==1
    assert db_session.query(GuestChatUsage).one().chat_messages==5
    assert generator.await_count==0


def test_stale_archive_hides_answers(auth_client,client,memorial,db_session):
    m,row,memory=seed(db_session,memorial);m.is_public=True;db_session.commit()
    assert publish(auth_client,row).status_code==200
    memory.content='Edited fact';db_session.commit()
    assert client.get(f'/api/v1/featured-answers/memorials/{m.id}/guest').json()==[]
    saved=auth_client.get(f'/api/v1/featured-answers/memorials/{m.id}/saved').json()
    assert saved[0]['stale'] and saved[0]['featured']
    assert publish(auth_client,row).status_code==409
    assert auth_client.put(f'/api/v1/featured-answers/saved/{row.id}',json={'publish_to_guests':False}).status_code==200


def test_private_invite_scope_expiry_revocation(auth_client,client,memorial,db_session):
    m,row,_=seed(db_session,memorial);m.is_public=False;db_session.commit()
    assert publish(auth_client,row).status_code==200
    invite=MemorialInvite(memorial_id=m.id,token='test-invite',permissions={'add_memories':True,'chat':False})
    db_session.add(invite);db_session.commit()
    url=f'/api/v1/featured-answers/memorials/{m.id}/guest'
    assert client.get(url).status_code==403
    assert client.get(url+'?invite_token=test-invite').status_code==403
    invite.permissions={'chat':True};db_session.commit()
    assert len(client.get(url+'?invite_token=test-invite').json())==1
    invite.expires_at=datetime.now(timezone.utc)-timedelta(days=1);db_session.commit()
    assert client.get(url+'?invite_token=test-invite').status_code==403
    db_session.delete(invite);db_session.commit()
    assert client.get(url+'?invite_token=test-invite').status_code==403


def test_owner_only_five_limit(auth_client,client,memorial,db_session,second_user_headers):
    m,row,_=seed(db_session,memorial)
    saved=f'/api/v1/featured-answers/memorials/{m.id}/saved'
    assert client.get(saved,headers={'Authorization':''}).status_code==401
    assert client.get(saved,headers=second_user_headers).status_code==403
    assert client.put(f'/api/v1/featured-answers/saved/{row.id}',headers=second_user_headers,json={'publish_to_guests':True}).status_code==403
    for i in range(6):
        _,candidate,_=seed(db_session,memorial,f'Question {i}')
        result=publish(auth_client,candidate,position=min(i,4))
        assert result.status_code==(200 if i<5 else 409),result.text
    assert db_session.query(FeaturedAvatarAnswer).count()==5
    assert all('source_memory_ids' in row for row in auth_client.get(saved).json())


def test_order_voice_change_and_foreign_invite(auth_client,client,memorial,db_session):
    m,first,_=seed(db_session,memorial,'First');m.is_public=True;db_session.commit()
    _,second,_=seed(db_session,memorial,'Second')
    assert publish(auth_client,first,position=0).status_code==200
    assert publish(auth_client,second,position=0).status_code==200
    url=f'/api/v1/featured-answers/memorials/{m.id}/guest'
    assert [r['question'] for r in client.get(url).json()]==['Second','First']
    assert publish(auth_client,first,position=0).status_code==200
    assert [r['question'] for r in client.get(url).json()]==['First','Second']
    other=Memorial(name='Other',owner_id=m.owner_id,is_public=False)
    db_session.add(other);db_session.flush()
    db_session.add(MemorialInvite(memorial_id=other.id,token='other-memorial',permissions={'chat':True}));db_session.commit()
    assert client.get(url+'?invite_token=other-memorial').status_code==403
    m.voice_id='changed-voice';db_session.commit()
    assert client.get(url).json()==[]
