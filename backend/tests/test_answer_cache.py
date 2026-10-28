from unittest.mock import AsyncMock
import pytest
from app.models import Memory, Memorial, AvatarAnswerCache
from app.schemas import AvatarChatRequest, AvatarChatResponse
from app.services.answer_cache import key_for, save_response, cached_response


@pytest.mark.asyncio
async def test_cached_answer_reuses_audio_and_revoice_only_calls_tts(db_session, registered_user, memorial, monkeypatch, tmp_path):
    from app.models import User
    import app.api.ai as api
    import app.services.ai_tasks as tasks
    monkeypatch.chdir(tmp_path)
    m = db_session.get(Memorial, memorial['id'])
    user = db_session.get(User, m.owner_id)
    memory = Memory(memorial_id=m.id, content='Original fact', status='approved')
    db_session.add(memory); db_session.commit()
    req = AvatarChatRequest(memorial_id=m.id, question='Same question?', include_audio=True, speech_style='calm')
    key = key_for(req, m, [memory], user)
    result = AvatarChatResponse(answer='Original fact.\n\nMore.', sources=['memory'], suggest_memory=False)
    save_response(db_session, key, req, m, user, result)
    row = db_session.query(AvatarAnswerCache).one()
    assert row.speech_markup['calm'].startswith('[calm]')
    assert '[calm]' not in row.response['answer']
    monkeypatch.setattr(api, '_resolve_tts_voice', lambda m: ('voice', 'fish_audio'))
    speech = AsyncMock(return_value=b'mp3')
    monkeypatch.setattr(tasks, 'generate_speech', speech)
    first = await cached_response(row, req, m, db_session)
    second = await cached_response(row, req, m, db_session)
    assert first.answer == second.answer == result.answer
    assert first.audio_url == second.audio_url
    assert speech.await_count == 1
    req.regenerate_audio = True
    third = await cached_response(row, req, m, db_session)
    assert third.answer == result.answer and third.audio_url != first.audio_url
    assert speech.await_count == 2
    assert row.audio_variants[next(k for k in row.audio_variants if not k.startswith('pending:'))]['url'] == first.audio_url
    from app.services.answer_cache import select_preview
    declined = select_preview(db_session, user, row.id, third.audio_preview_id, False)
    assert declined['audio_url'] is None
    assert (await cached_response(row, req.model_copy(update={'regenerate_audio': False}), m, db_session)).audio_url == first.audio_url
    fourth = await cached_response(row, req, m, db_session)
    selected = select_preview(db_session, user, row.id, fourth.audio_preview_id, True)
    assert selected['audio_url'] == fourth.audio_url
    assert (await cached_response(row, req.model_copy(update={'regenerate_audio': False}), m, db_session)).audio_url == fourth.audio_url
    assert speech.await_count == 3
    fifth = await cached_response(row, req, m, db_session)
    memory.content = 'Changed fact'
    db_session.commit()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as failure:
        select_preview(db_session, user, row.id, fifth.audio_preview_id, True)
    assert failure.value.status_code == 409
    assert key_for(req, m, [memory], user) != key
    req.question = 'Different question'
    assert key_for(req, m, [memory], user) != key


def test_chat_repeats_without_llm_and_rejects_stale_revoice(auth_client, memorial, db_session, monkeypatch):
    import app.api.ai as api
    db_session.add(Memory(memorial_id=memorial['id'], content='Approved fact', status='approved'))
    db_session.commit()
    generate = AsyncMock(return_value=('Approved fact', []))
    # Return a source ID so this is a grounded, cacheable answer.
    memory = db_session.query(Memory).filter_by(memorial_id=memorial['id']).first()
    generate.return_value = ('Approved fact', [f'memory_{memory.id}'])
    monkeypatch.setattr(api, 'generate_rag_response', generate)
    req = {'memorial_id': memorial['id'], 'question': 'Что ты помнишь о себе?'}
    first = auth_client.post('/api/v1/ai/avatar/chat', json=req)
    assert first.status_code == 200, first.text
    second = auth_client.post('/api/v1/ai/avatar/chat', json=req)
    assert second.status_code == 200, second.text
    assert second.json()['answer'] == first.json()['answer']
    assert generate.await_count == 1
    memory.content = 'Changed approved fact'; db_session.commit()
    stale = auth_client.post('/api/v1/ai/avatar/chat', json={**req, 'include_audio': True, 'regenerate_audio': True})
    assert stale.status_code == 409, stale.text
    assert generate.await_count == 1


def test_revoice_does_not_spend_text_question_quota(auth_client, memorial, db_session, monkeypatch, tmp_path):
    from app.models import User, UserUsage
    import app.api.ai as api
    import app.services.ai_tasks as tasks
    monkeypatch.chdir(tmp_path)
    m = db_session.get(Memorial, memorial['id'])
    user = db_session.get(User, m.owner_id)
    memory = Memory(memorial_id=m.id, content='Fact', status='approved')
    db_session.add(memory); db_session.commit()
    request = AvatarChatRequest(memorial_id=m.id, question='Question')
    save_response(db_session, key_for(request, m, [memory], user), request, m, user,
                  AvatarChatResponse(answer='Fact', sources=['memory']))
    monkeypatch.setattr(api, '_resolve_tts_voice', lambda m: ('voice', 'fish_audio'))
    speech = AsyncMock(return_value=b'mp3')
    monkeypatch.setattr(tasks, 'generate_speech', speech)
    response = auth_client.post('/api/v1/ai/avatar/chat', json={
        'memorial_id': m.id, 'question': 'Question', 'include_audio': True, 'regenerate_audio': True})
    assert response.status_code == 200, response.text
    assert response.json()['answer'] == 'Fact'
    assert sum(row.chat_messages for row in db_session.query(UserUsage).all()) == 0
    assert speech.await_count == 1
    body = response.json()
    route = f'/api/v1/ai/avatar/audio-preview/{body["answer_cache_id"]}/{body["audio_preview_id"]}'
    assert auth_client.post(route, json={'accept': True}, headers={'Authorization': ''}).status_code == 401
    accepted = auth_client.post(route, json={'accept': True})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()['audio_url'] == body['audio_url']
    assert auth_client.post(route, json={'accept': True}).status_code == 404


@pytest.mark.parametrize('style,cue', [
    ('natural', ''), ('calm', '[calm]'), ('warm', '[warm, gentle tone]'),
    ('happy', '[happy]'), ('sad', '[sad]'), ('nostalgic', '[nostalgic]'),
])
def test_emotion_choice_marks_speech_without_changing_written_answer(style, cue):
    from app.services.answer_cache import speech_text
    written = 'Один и тот же текст.\n\nСледующее предложение.'
    request = AvatarChatRequest(memorial_id=1, question='Test', speech_style=style)
    spoken = speech_text(written, request.speech_style)
    assert spoken.startswith(cue)
    assert '[pause]' in spoken
    assert '[' not in written
    if cue:
        assert spoken.removeprefix(cue).strip() == 'Один и тот же текст. [pause] Следующее предложение.'
