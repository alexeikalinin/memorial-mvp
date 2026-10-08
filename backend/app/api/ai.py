"""
API endpoints для AI-функций: анимация фото и чат с аватаром.
"""
import logging
import asyncio

from fastapi import Response, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pathlib import Path

import httpx

from app.services.voice_samples import prepare_voice_samples, clean_voice_sample

from app.db import get_db
from app.auth import get_current_user, get_optional_user, get_optional_authenticated_user, require_actual_memorial_owner
from app.models import Memorial, Media, Memory, MediaType, FamilyRelationship, User, UserRole, MemorialInvite, GuestChatUsage
from app.services.billing import (
    check_chat_quota,
    check_animation_quota,
    check_tts_access,
    check_family_rag_access,
    check_live_session_quota,
    _get_or_create_usage,
    is_demo_account,
    increment_animation_usage,
    increment_live_session_usage,
    get_limits,
    _effective_plan,
)
from app.schemas import (
    PhotoAnimateRequest,
    PhotoAnimateResponse,
    AvatarChatRequest,
    AvatarChatResponse,
    AnimationStatusRequest,
    AnimationStatusResponse,
    ElevenLabsQuotaResponse,
    LiveSessionStartRequest,
    LiveSessionStartResponse,
)
from app.services.ai_tasks import (
    get_embedding,
    generate_rag_response,
    search_similar_memories,
    generate_speech,
    create_custom_voice,
    delete_custom_voice,
    animate_photo as animate_photo_service,
    get_animation_status,
    sync_family_memories,
)
from app.workers.worker import animate_photo_task, create_memory_embedding_task
from app.services.s3_service import upload_file_to_s3, get_public_url
from app.config import settings
import os
import uuid
import tempfile

router = APIRouter(prefix="/ai", tags=["ai"])


def _resolve_tts_voice(memorial):
    if memorial.voice_id:
        return memorial.voice_id, memorial.voice_provider or "elevenlabs"
    if settings.TTS_PROVIDER == "fish_audio":
        return None, "fish_audio"
    if memorial.voice_gender == "male" and settings.ELEVENLABS_VOICE_ID_MALE:
        return settings.ELEVENLABS_VOICE_ID_MALE, "elevenlabs"
    if memorial.voice_gender == "female" and settings.ELEVENLABS_VOICE_ID_FEMALE:
        return settings.ELEVENLABS_VOICE_ID_FEMALE, "elevenlabs"
    return settings.ELEVENLABS_VOICE_ID, "elevenlabs"


@router.get("/tts/status")
async def get_tts_status(
    memorial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.auth import require_memorial_access
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.VIEWER, allow_public=True)
    _, provider = _resolve_tts_voice(memorial)
    key = settings.FISH_AUDIO_API_KEY if provider == "fish_audio" else settings.ELEVENLABS_API_KEY
    return {"provider": provider, "configured": bool(key), "has_custom_voice": bool(memorial.voice_id)}


@router.post("/photo/animate", response_model=PhotoAnimateResponse)
async def animate_photo(
    request: PhotoAnimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Запустить задачу оживления фото через D-ID или HeyGen.
    Задача выполняется в фоновом режиме через Celery worker.
    Требует авторизации; квота: 5 рендеров/месяц на Plus/Lifetime, 0 на Free.
    """
    check_animation_quota(current_user, db)

    # Проверка существования медиа
    media = db.query(Media).filter(Media.id == request.media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    if media.media_type != MediaType.PHOTO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media is not a photo"
        )
    
    if media.is_animated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo is already animated"
        )
    
    # Providers receive the prepared JPEG, never the original gallery file.
    image_url = f"{(settings.PUBLIC_API_URL or 'http://localhost:8000').rstrip('/')}/api/v1/media/avatar/{media.id}.jpg"

    # Запуск фоновой задачи
    try:
        task = animate_photo_task.delay(
            media_id=request.media_id,
            image_url=image_url,
            script=request.prompt
        )
        
        provider = "heygen" if settings.USE_HEYGEN else "d-id"
        increment_animation_usage(current_user, db)
        return PhotoAnimateResponse(
            task_id=task.id,
            status="pending",
            provider=provider,
            message=f"Animation task started with {provider}. Check status later."
        )
    except HTTPException:
        raise
    except Exception as e:
        # Обработка ошибок Redis/Celery
        error_msg = str(e)
        if "Connection refused" in error_msg or "redis" in error_msg.lower() or "OperationalError" in error_msg:
            # Fallback: попытка синхронного выполнения (не рекомендуется для production)
            # Для MVP можно использовать, но лучше запустить Redis
            try:
                # Прямой вызов функции анимации (await — уже в async-контексте FastAPI)
                from app.services.ai_tasks import animate_photo as _animate_photo_svc

                result = await _animate_photo_svc(image_url, request.prompt)
                provider = result.get("provider", "heygen" if settings.USE_HEYGEN else "d-id")
                task_id = result.get("task_id")

                # Сохраняем task_id в БД
                media.animation_task_id = task_id
                db.commit()
                increment_animation_usage(current_user, db)
                return PhotoAnimateResponse(
                    task_id=task_id or "sync",
                    status="processing",
                    message=f"Animation started synchronously with {provider} (Redis not available). This may take longer."
                )
            except Exception as sync_error:
                error_detail = str(sync_error)
                print(f"Error in sync animation: {error_detail}")
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Redis/Celery worker не запущен. Для анимации фото необходимо запустить Redis и Celery worker. См. документацию. Ошибка: {error_detail[:200]}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при запуске задачи анимации: {error_msg[:200]}"
            )


@router.post("/avatar/chat", response_model=AvatarChatResponse)
async def avatar_chat(
    request: AvatarChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_authenticated_user),
    invite_token: Optional[str] = Query(None),
    guest_id: Optional[str] = Query(None, min_length=16, max_length=64, pattern=r"^[a-zA-Z0-9-]+$"),
):
    guest = None
    if not current_user:
        if not guest_id:
            raise HTTPException(status_code=401, detail={"code": "guest_identity_required"})
        guest = db.query(GuestChatUsage).filter_by(guest_id=guest_id, memorial_id=request.memorial_id).first()
        if guest and guest.chat_messages >= 5:
            raise HTTPException(status_code=401, detail={"code": "guest_chat_limit", "limit": 5, "registered_limit": 15})
    result = await _avatar_chat_response(request, db, current_user, invite_token)
    if current_user:
        from app.models import UserUsage
        usage = _get_or_create_usage(current_user.id, db)
        query = db.query(UserUsage).filter(UserUsage.id == usage.id)
        if not is_demo_account(current_user):
            query = query.filter(UserUsage.chat_messages < get_limits(current_user)["chat_messages_per_month"])
        if not query.update({UserUsage.chat_messages: UserUsage.chat_messages + 1}, synchronize_session=False):
            db.rollback()
            raise HTTPException(status_code=402, detail="Monthly question limit reached. Choose a plan to continue.")
        db.commit()
    else:
        if guest is None:
            guest = GuestChatUsage(guest_id=guest_id, memorial_id=request.memorial_id, chat_messages=0)
            db.add(guest)
            try:
                db.flush()
            except Exception:
                db.rollback()
                guest = db.query(GuestChatUsage).filter_by(guest_id=guest_id, memorial_id=request.memorial_id).first()
                if guest is None:
                    raise
        changed = db.query(GuestChatUsage).filter(GuestChatUsage.id == guest.id, GuestChatUsage.chat_messages < 5).update(
            {GuestChatUsage.chat_messages: GuestChatUsage.chat_messages + 1}, synchronize_session=False)
        if not changed:
            db.rollback()
            raise HTTPException(status_code=401, detail={"code": "guest_chat_limit", "limit": 5, "registered_limit": 15})
        db.commit()
        db.refresh(guest)
        result.guest_questions_remaining = max(0, 5 - guest.chat_messages)
    return result


async def _avatar_chat_response(
    request: AvatarChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
    invite_token: Optional[str] = Query(None),
):
    """
    Чат с ИИ-аватаром на основе RAG (Retrieval-Augmented Generation).

    Процесс:
    1. Получить все воспоминания мемориала
    2. Создать embedding вопроса
    3. Найти релевантные фрагменты через векторный поиск (Pinecone)
    4. Сформировать ответ через OpenAI с этичным промптом
    5. Опционально: сгенерировать аудио через ElevenLabs
    """
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == request.memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )

    from app.auth import require_memorial_access
    from datetime import datetime
    if invite_token:
        invite = db.query(MemorialInvite).filter(MemorialInvite.token == invite_token).first()
        if (not invite or invite.memorial_id != memorial.id
                or (invite.expires_at and invite.expires_at.replace(tzinfo=None) < datetime.utcnow())
                or not (invite.permissions or {}).get("chat")):
            raise HTTPException(status_code=403, detail="Invalid or expired chat invitation")
    elif not memorial.is_public:
        require_memorial_access(memorial.id, current_user, db, min_role=UserRole.VIEWER)
    # QR/invite visitors receive text chat only, even after registering.
    owner = False
    if current_user:
        try:
            require_actual_memorial_owner(memorial.id, current_user, db)
            owner = True
        except HTTPException:
            pass
    if not owner and (request.include_audio or request.include_family_memories):
        raise HTTPException(status_code=403, detail="Visitors can ask text questions only")

    # ── Billing checks (authenticated users only) ──────────────────────────────
    if current_user:
        check_chat_quota(current_user, request.memorial_id, db)
        if request.include_family_memories:
            check_family_rag_access(current_user)
        if request.include_audio:
            check_tts_access(current_user)
    else:
        # Unauthenticated users on public memorials: no TTS or family RAG
        if request.include_audio:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Voice replies require a Plus or Lifetime account. Please sign in.",
            )
        if request.include_family_memories:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Family RAG requires a Plus account. Please sign in.",
            )
    # ─────────────────────────────────────────────────────────────────────────

    # Определяем список мемориалов для RAG-поиска (основной + родственники)
    search_memorial_ids = [request.memorial_id]
    family_memorial_map = {}  # {memorial_id: (name, relationship_type)}

    if request.include_family_memories:
        family_rels = db.query(FamilyRelationship).filter(
            FamilyRelationship.memorial_id == request.memorial_id
        ).all()
        for rel in family_rels:
            related = db.query(Memorial).filter(
                Memorial.id == rel.related_memorial_id
            ).first()
            if related:
                search_memorial_ids.append(rel.related_memorial_id)
                family_memorial_map[rel.related_memorial_id] = (
                    related.name,
                    rel.relationship_type.value,
                )

    # Получаем все воспоминания (не только с embeddings)
    all_memories = db.query(Memory).filter(
        Memory.memorial_id == request.memorial_id,
        Memory.status == "approved",
    ).all()
    
    if not all_memories:
        no_mem_msg = (
            "I don't have any memories yet. Please add some memories so I can answer questions."
            if request.language == "en" else
            "У меня пока нет информации об этом человеке. Пожалуйста, добавьте воспоминания, чтобы я мог отвечать на вопросы."
        )
        return AvatarChatResponse(answer=no_mem_msg, sources=[])
    
    # Проверяем, есть ли воспоминания с embeddings
    # Важно: используем новый запрос к БД, чтобы избежать проблем с кэшем сессии
    # Сначала проверяем через прямой SQL запрос
    from sqlalchemy import text
    result = db.execute(
        text("SELECT id, embedding_id FROM memories WHERE memorial_id = :memorial_id"),
        {"memorial_id": request.memorial_id}
    )
    memory_embeddings_map = {row[0]: row[1] for row in result}
    
    # Теперь проверяем объекты с учетом данных из БД
    memories_with_embeddings = []
    for m in all_memories:
        # Обновляем объект из БД
        db.refresh(m)
        # Также проверяем через прямой запрос
        db_embedding_id = memory_embeddings_map.get(m.id)
        
        # Используем embedding_id из БД, если он есть
        embedding_id_to_check = db_embedding_id if db_embedding_id else m.embedding_id
        
        # Проверяем embedding_id
        has_embedding = False
        if embedding_id_to_check:
            if isinstance(embedding_id_to_check, str):
                has_embedding = bool(embedding_id_to_check.strip())
            else:
                has_embedding = bool(embedding_id_to_check)
        
        if has_embedding:
            # Обновляем объект, если embedding_id был в БД, но не в объекте
            if db_embedding_id and not m.embedding_id:
                m.embedding_id = db_embedding_id
            memories_with_embeddings.append(m)
    
    print(f"Total memories: {len(all_memories)}, with embeddings: {len(memories_with_embeddings)}")
    for m in all_memories:
        db_emb = memory_embeddings_map.get(m.id)
        print(f"  Memory {m.id}: obj.embedding_id={repr(m.embedding_id)}, db.embedding_id={repr(db_emb)}")
    
    # Если есть воспоминания без embeddings, пытаемся создать их
    if len(memories_with_embeddings) < len(all_memories):
        from app.services.ai_tasks import upsert_memory_embedding
        
        created = 0
        errors = []
        for memory in all_memories:
            # Проверяем, что embedding_id действительно отсутствует
            has_embedding = False
            if memory.embedding_id:
                if isinstance(memory.embedding_id, str):
                    has_embedding = bool(memory.embedding_id.strip())
                else:
                    has_embedding = bool(memory.embedding_id)
            
            if not has_embedding:
                try:
                    # Используем get_embedding, который уже импортирован в начале функции
                    embedding = await get_embedding(memory.content)
                    vector_id = await upsert_memory_embedding(
                        memory_id=memory.id,
                        memorial_id=request.memorial_id,
                        text=memory.content,
                        embedding=embedding,
                        title=memory.title
                    )
                    memory.embedding_id = vector_id
                    created += 1
                    print(f"Created embedding for memory {memory.id}: {vector_id}")
                except Exception as e:
                    error_msg = f"Failed to create embedding for memory {memory.id}: {str(e)}"
                    print(f"Warning: {error_msg}")
                    errors.append(error_msg)
        
        if created > 0:
            try:
                db.commit()
                print(f"✅ Committed {created} embeddings to database")
                # Сбрасываем кэш сессии и перезагружаем объекты
                db.expire_all()
                # Перезагружаем все объекты из БД
                for memory in all_memories:
                    db.refresh(memory)
                # Пересчитываем список с embeddings
                memories_with_embeddings = []
                for m in all_memories:
                    db.refresh(m)
                    if m.embedding_id and (isinstance(m.embedding_id, str) and m.embedding_id.strip() or m.embedding_id):
                        memories_with_embeddings.append(m)
                print(f"✅ After refresh: {len(memories_with_embeddings)} memories with embeddings")
            except Exception as commit_error:
                print(f"❌ ERROR committing embeddings: {commit_error}")
                import traceback
                traceback.print_exc()
                db.rollback()
        
        # Если были ошибки, логируем их
        if errors:
            print(f"Errors creating embeddings: {errors}")
    
    # Используем только воспоминания с embeddings для поиска
    memories = memories_with_embeddings
    
    try:
        # Создание embedding вопроса
        question_embedding = await get_embedding(request.question)
        
        # Поиск релевантных воспоминаний в векторной БД
        # Понижаем порог для лучшего поиска, особенно для общих вопросов
        similar_memories = await search_similar_memories(
            memorial_ids=search_memorial_ids,
            query_embedding=question_embedding,
            top_k=5,
            min_score=0.1  # Низкий порог — длинные тексты дают размытые embeddings
        )
        
        print(f"🔍 Found {len(similar_memories)} similar memories for question: '{request.question}'")
        for i, mem in enumerate(similar_memories):
            print(f"  {i+1}. Memory ID: {mem.get('memory_id')}, Score: {mem.get('score', 0):.3f}, Title: {mem.get('title', 'N/A')}")
        
        # ВАЖНО: Всегда получаем полный текст из БД, так как в векторной БД
        # текст может быть обрезанным (например, только 1000 символов в Qdrant payload)
        context_chunks = []
        has_family_context = False
        for mem in similar_memories:
            memory_id = mem.get("memory_id")
            source_memorial_id = mem.get("source_memorial_id")
            if memory_id:
                # Всегда получаем полный текст из БД для гарантии полноты контекста
                memory = db.query(Memory).filter(Memory.id == memory_id, Memory.status == "approved", Memory.memorial_id.in_(search_memorial_ids)).first()
                if memory:
                    text = memory.content
                    # Добавляем метку, если воспоминание от родственника
                    if source_memorial_id and source_memorial_id != request.memorial_id and source_memorial_id in family_memorial_map:
                        rel_name, rel_type = family_memorial_map[source_memorial_id]
                        if request.language == "en":
                            label = f"[From memories of {rel_name} ({rel_type})]: "
                        else:
                            label = f"[Из воспоминаний {rel_name} ({rel_type})]: "
                        text = label + text
                        has_family_context = True
                    context_chunks.append({
                        "text": text,
                        "memory_id": memory.id,
                        "score": mem.get("score", 0),
                        "title": memory.title,
                        "source_memorial_id": source_memorial_id,
                    })
                    print(f"✅ Added context chunk: Memory #{memory.id}, text length: {len(memory.content)} chars")
                else:
                    print(f"⚠️ Memory {memory_id} not found in database")
            elif mem.get("text"):
                # Fallback: если memory_id нет, используем текст из payload
                # (но это не должно происходить в нормальной работе)
                context_chunks.append(mem)
                print(f"⚠️ Using text from payload (no memory_id): {len(mem.get('text', ''))} chars")
        
        # Fallback: векторный поиск пуст (часто на проде — новый пустой Qdrant/volume при той же Postgres,
        # или порог score отфильтровал всё), хотя воспоминания в БД есть.
        if not context_chunks and all_memories:
            print(
                f"⚠️ RAG returned no usable chunks; falling back to DB memories only "
                f"(memorial_id={request.memorial_id}, count={len(all_memories)})"
            )
            max_chars = 18000
            used = 0
            for m in sorted(all_memories, key=lambda x: x.id, reverse=True):
                if used >= max_chars:
                    break
                piece = (m.content or "").strip()
                if not piece:
                    continue
                take = piece[: max_chars - used]
                context_chunks.append({
                    "text": take,
                    "memory_id": m.id,
                    "score": 0.35,
                    "title": m.title,
                    "source_memorial_id": request.memorial_id,
                })
                used += len(take)
        
        if not context_chunks:
            print(f"❌ No context chunks after RAG + DB fallback (similar_hits={len(similar_memories)})")
            no_info_msg = (
                "I don't have memories about that."
                if request.language == "en" else
                "У меня нет информации на эту тему."
            )
            return AvatarChatResponse(answer=no_info_msg, sources=[])
        
        print(f"📝 Created {len(context_chunks)} context chunks for RAG")
        
        # Strict archive mode does not synthesize a fictional personality.
        # Confirmed visitor labels below may influence addressing only.
        persona_prompt = None

        # Nickname: если текущий пользователь связан с этим мемориалом и задал обращение
        if current_user:
            visitor_rel = db.query(FamilyRelationship).filter(
                FamilyRelationship.related_memorial_id == request.memorial_id,
                FamilyRelationship.nickname_for_visitor.isnot(None),
                FamilyRelationship.nickname_for_visitor != "",
            ).join(
                Memorial, Memorial.id == FamilyRelationship.memorial_id
            ).filter(
                Memorial.owner_id == current_user.id
            ).first()
            if visitor_rel and visitor_rel.nickname_for_visitor:
                nick = visitor_rel.nickname_for_visitor.strip()
                if request.language == "en":
                    nick_note = (
                        f'\n\nThe person speaking with you is a close relative. You used to call them "{nick}". '
                        f'Use this name naturally — greet them by name in your very first reply, '
                        f'then use it occasionally when it feels warm and natural, not in every sentence.'
                    )
                else:
                    nick_note = (
                        f'\n\nС тобой разговаривает близкий родственник. Ты обращался к нему "{nick}". '
                        f'Используй это имя естественно — обратись по имени в самом первом ответе, '
                        f'затем изредка, когда это звучит тепло и уместно, но не в каждой фразе.'
                    )
                persona_prompt = (persona_prompt or "") + nick_note

        # Если в контексте есть воспоминания родственников — дополняем system prompt
        if has_family_context:
            if request.language == "en":
                family_note = (
                    "\n\nSome memories in the context belong to family members "
                    "(marked \"[From memories of ...]\"). "
                    "Use them as events you remember or heard from loved ones. "
                    "Don't claim others' memories as your own: say \"we together...\" "
                    "or \"according to my wife/husband/son...\"."
                )
            else:
                family_note = (
                    "\n\nНекоторые воспоминания в контексте принадлежат родственникам "
                    "(помечены \"[Из воспоминаний ...]\"). "
                    "Используй их как события, о которых ты помнишь или знаешь от близких. "
                    "Не приписывай чужие воспоминания себе напрямую: скажи \"мы вместе...\" "
                    "или \"по словам жены/мужа/сына...\"."
                )
            if persona_prompt:
                persona_prompt = persona_prompt + family_note
            else:
                persona_prompt = family_note

        # Генерация ответа через OpenAI с улучшенным RAG
        answer, source_ids = await generate_rag_response(
            question=request.question,
            context_chunks=context_chunks,
            memorial_name=memorial.name,
            system_prompt=persona_prompt,
            language=request.language,
        )
        
        # Формируем читаемые источники (язык подписи = язык запроса)
        mem_label = "Memory" if request.language == "en" else "Воспоминание"
        sources = []
        for chunk in context_chunks:
            memory_id = chunk.get("memory_id")
            title = chunk.get("title", "")
            if memory_id and f"memory_{memory_id}" in source_ids:
                source_text = f"{mem_label} #{memory_id}"
                if title:
                    source_text += f": {title}"
                sources.append(source_text)
        
        # Опциональная генерация аудио
        audio_url = None
        audio_error = None
        if request.include_audio:
            try:
                voice_id, voice_provider = _resolve_tts_voice(memorial)
                if voice_provider == "elevenlabs" and not voice_id:
                    raise ValueError("Не задан голос ElevenLabs. Загрузите клон голоса аватара.")

                if voice_provider == "fish_audio" and not settings.FISH_AUDIO_API_KEY:
                    raise ValueError("В backend/.env не задан FISH_AUDIO_API_KEY.")
                if voice_provider == "elevenlabs" and not settings.ELEVENLABS_API_KEY:
                    raise ValueError("В backend/.env не задан ELEVENLABS_API_KEY.")
                audio_bytes = await generate_speech(answer, voice_id=voice_id, provider=voice_provider, speed=request.speech_speed, pronunciations=request.pronunciations)

                # Сохранение аудио-файла
                audio_dir = Path("uploads/audio")
                audio_dir.mkdir(exist_ok=True)
                audio_filename = f"chat_{request.memorial_id}_{hash(request.question)}.mp3"
                audio_path = audio_dir / audio_filename

                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)

                # URL для воспроизведения в браузере: только HTTP(S) или путь к API (никогда s3://)
                if settings.USE_S3 and settings.supabase_public_url:
                    s3_key = f"audio/{audio_filename}"
                    if upload_file_to_s3(audio_path, s3_key, "audio/mpeg"):
                        public_url = get_public_url(s3_key)
                        audio_url = public_url if (public_url and public_url.startswith("http")) else f"/api/v1/media/audio/{audio_filename}"
                    else:
                        audio_url = f"/api/v1/media/audio/{audio_filename}"
                else:
                    audio_url = f"/api/v1/media/audio/{audio_filename}"
                # PUBLIC_API_URL используется только для D-ID/HeyGen (им нужен публичный URL),
                # но НЕ для браузера — браузер получает относительный /api/v1/... через Vite прокси

            except Exception as e:
                audio_error = str(e)
                print(f"Error generating audio: {e}")

        # Запуск анимации говорящей головы (async, опционально)
        animation_task_id = None
        animation_provider = None
        avatar_source_id = (memorial.portrait_settings or {}).get("avatar", {}).get("media_id") or memorial.cover_photo_id
        if audio_url and avatar_source_id:
            try:
                cover_media = db.query(Media).filter(Media.id == avatar_source_id).first()
                if cover_media:
                    public_image_url = f"{(settings.PUBLIC_API_URL or 'http://localhost:8000').rstrip('/')}/api/v1/media/portrait/{memorial.id}/avatar.jpg"
                    # Формируем публичный audio_url для D-ID (нужен абсолютный URL)
                    if audio_url.startswith("/"):
                        public_audio_url = f"{settings.PUBLIC_API_URL}{audio_url}"
                    else:
                        public_audio_url = audio_url
                    anim_result = await animate_photo_service(
                        image_url=public_image_url,
                        script=answer,
                        audio_url=public_audio_url,
                    )
                    animation_task_id = anim_result.get("task_id")
                    animation_provider = anim_result.get("provider")
                    print(f"✅ Animation started: task_id={animation_task_id}, provider={animation_provider}")
            except Exception as e:
                # Анимация опциональна — не ломаем чат при ошибке
                print(f"Warning: could not start animation: {e}")

        return AvatarChatResponse(
            answer=answer,
            audio_url=audio_url,
            audio_error=audio_error,
            animation_task_id=animation_task_id,
            animation_provider=animation_provider,
            sources=sources
        )
    
    except Exception as e:
        logging.exception("avatar_chat failed")
        msg = str(e)
        low = msg.lower()
        detail = f"Error processing chat request: {msg}"
        is_config = False
        if "openai_api_key not configured" in low or (
            "openai_api_key" in low and "not configured" in low
        ):
            detail += " Set OPENAI_API_KEY in the backend environment (Railway Variables)."
            is_config = True
        elif (
            settings.VECTOR_DB_PROVIDER == "qdrant"
            and not settings.QDRANT_LOCAL_PATH
            and (
                "connection refused" in low
                or "connection error" in low
                or "failed to establish a new connection" in low
                or "name or service not known" in low
                or "timed out" in low
                or "6333" in msg
                or ("localhost" in low and "6333" in msg)
                or ("127.0.0.1" in msg and "6333" in msg)
            )
        ):
            detail += (
                " Qdrant is not reachable from this host (localhost:6333 does not work on Railway). "
                "Create a cluster at https://cloud.qdrant.io and set QDRANT_URL + QDRANT_API_KEY; "
                "leave QDRANT_LOCAL_PATH empty. Re-create memory embeddings against that cluster if needed."
            )
            is_config = True
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
                if is_config
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=detail,
        )


@router.post("/animation/status", response_model=AnimationStatusResponse)
async def get_animation_status_endpoint(
    request: AnimationStatusRequest,
    db: Session = Depends(get_db),
):
    """
    Проверить статус задачи анимации фото.
    
    Если provider не указан, определяется автоматически из записи в БД.
    task_id может быть либо Celery task ID, либо HeyGen/D-ID video_id.
    """
    # Валидация входных данных
    if not request.task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_id is required"
        )
    
    # Определяем provider
    provider = request.provider
    if not provider:
        provider = "heygen" if settings.USE_HEYGEN else "d-id"
    
    # Проблема: request.task_id может быть Celery task ID, а не HeyGen video_id
    # Worker сохраняет HeyGen video_id в media.animation_task_id
    # Нужно найти media и получить video_id из БД
    
    video_id = request.task_id  # По умолчанию используем task_id
    
    # Если указан media_id, используем его для поиска
    if request.media_id:
        media = db.query(Media).filter(Media.id == request.media_id).first()
        if media and media.animation_task_id:
            video_id = media.animation_task_id
            print(f"Using media_id={request.media_id}, found video_id in DB: {video_id}")
        else:
            print(f"Media {request.media_id} not found or animation_task_id is None")
    else:
        # Пытаемся найти media по animation_task_id (может быть уже HeyGen video_id)
        media = db.query(Media).filter(Media.animation_task_id == request.task_id).first()
        if media and media.animation_task_id:
            video_id = media.animation_task_id
            print(f"Found media by animation_task_id, using video_id: {video_id}")
        else:
            # Не нашли - возможно task_id это уже HeyGen video_id
            print(f"Media not found, using task_id as video_id: {request.task_id}")
    
    print(f"Checking animation status: provider={provider}, video_id={video_id}")
    
    try:
        status_result = await get_animation_status(provider, video_id)
        
        # Проверяем, что status_result - это словарь
        if not isinstance(status_result, dict):
            print(f"Warning: get_animation_status returned non-dict: {type(status_result)}")
            status_result = {
                "status": "processing",
                "video_url": None,
                "error": None
            }
        
        anim_status = status_result.get("status", "unknown")
        error = status_result.get("error")
        
        # Не возвращаем error, если статус processing/pending (это нормально)
        if anim_status in ("processing", "pending") and error:
            error = None
        
        return AnimationStatusResponse(
            task_id=request.task_id,  # Возвращаем оригинальный task_id для совместимости
            status=anim_status,
            video_url=status_result.get("video_url"),
            error=error,
            provider=provider
        )
    
    except ValueError as e:
        error_msg = str(e)
        print(f"ValueError in get_animation_status_endpoint: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        error_msg = str(e)
        print(f"Exception in get_animation_status_endpoint: {error_msg}")
        import traceback
        traceback.print_exc()
        # Возвращаем ошибку в формате ответа, а не выбрасываем исключение
        return AnimationStatusResponse(
            task_id=request.task_id,
            status="error",
            video_url=None,
            error=f"Error checking animation status: {error_msg}",
            provider=provider
        )


@router.post("/voice/prepare")
async def prepare_voice_preview(
    memorial_id: int,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return an ephemeral cleaned sample. No provider call or model change."""
    require_actual_memorial_owner(memorial_id, current_user, db)
    paths = []
    try:
        paths = await prepare_voice_samples([audio_file], Path("uploads/voices"))
        output = paths[0].with_name(paths[0].stem + "_clean.mp3")
        paths.append(output)
        await clean_voice_sample(paths[0], output)
        return Response(output.read_bytes(), media_type="audio/mpeg", headers={"Cache-Control": "no-store"})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=400, detail='Обработка заняла слишком много времени. Выберите более короткую запись.') from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        for path in paths:
            path.unlink(missing_ok=True)


@router.post("/voice/upload")
async def upload_voice(
    memorial_id: int,
    audio_files: List[UploadFile] = File(...),
    voice_name: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Загрузить аудиозаписи или видео с голосом и создать кастомный
    клонированный голос. Доступно только на тарифах Plus и Lifetime memorial.

    Args:
        audio_files: один или несколько образцов голоса (до 20). Несколько
            разных по интонации чистых записей дают более стабильный и точный клон,
            чем один файл — используйте это, если у пользователя есть несколько
            голосовых сообщений (Telegram/WhatsApp/Viber и т.п.).
        provider: "elevenlabs" | "fish_audio". По умолчанию — settings.TTS_PROVIDER.
            Провайдер сохраняется вместе с voice_id и используется для всех
            последующих TTS-запросов этого мемориала.

    Требования к аудио:
    - Аудио: MP3, WAV, M4A, OGG/OGA; видео: MP4, MOV, M4V, WEBM.
    - Видео до 10 минут; до 100 МБ на файл; аудиодорожка извлекается сервером.
    - Суммарная длительность: минимум 1 минута чистой речи (рекомендуется)
    - Качество: без посторонних шумов
    """
    from app.auth import require_memorial_access
    require_actual_memorial_owner(memorial_id, current_user, db)
    check_tts_access(current_user)
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )

    if not audio_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one audio file is required"
        )
    if len(audio_files) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Максимум 20 аудио-образцов за раз"
        )

    # Video stays on our server; providers receive the extracted MP3 only.
    try:
        temp_paths = await prepare_voice_samples(audio_files, Path("uploads/voices"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    def _cleanup():
        for p in temp_paths:
            if p.exists():
                p.unlink()

    # Запоминаем старый голос до перезаписи — после успешного клонирования удалим его
    # у провайдера, чтобы не копились неиспользуемые модели в аккаунте.
    old_voice_id = memorial.voice_id
    old_voice_provider = memorial.voice_provider

    try:
        # Создаем кастомный клонированный голос через выбранного провайдера
        voice_provider_final = provider if provider in ("elevenlabs", "fish_audio") else settings.TTS_PROVIDER
        voice_name_final = voice_name or f"{memorial.name} Voice"
        voice_id = await create_custom_voice(
            audio_file_paths=[str(p) for p in temp_paths],
            voice_name=voice_name_final,
            description=f"Custom voice for {memorial.name}",
            provider=voice_provider_final,
        )

        # Сохраняем voice_id и провайдера в мемориал (без провайдера voice_id непереносим между сервисами)
        memorial.voice_id = voice_id
        memorial.voice_provider = voice_provider_final
        db.commit()
        db.refresh(memorial)

        _cleanup()

        # Удаляем старую модель голоса (best-effort — ошибка здесь не должна ломать ответ,
        # новый голос уже сохранён и рабочий)
        if old_voice_id and old_voice_id != voice_id:
            try:
                await delete_custom_voice(old_voice_id, old_voice_provider)
            except Exception as cleanup_err:
                print(f"Warning: failed to delete old voice {old_voice_id}: {cleanup_err}")

        return {
            "success": True,
            "voice_id": voice_id,
            "voice_name": voice_name_final,
            "voice_provider": voice_provider_final,
            "samples_used": len(temp_paths),
            "message": f"Голос успешно создан и сохранен для мемориала '{memorial.name}'"
        }

    except ValueError as e:
        _cleanup()
        error_str = str(e)
        # Понятное сообщение для платного плана ElevenLabs
        if "paid_plan_required" in error_str or "payment_required" in error_str or "instant_voice_cloning" in error_str:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Клонирование голоса требует платного плана ElevenLabs. Обновите подписку на elevenlabs.io или используйте стандартный голос аватара."
            )
        if voice_provider_final == "fish_audio" and ("401" in error_str or "not configured" in error_str):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Клонирование голоса через Fish Audio недоступно: проверьте FISH_AUDIO_API_KEY и тариф на fish.audio."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_str
        )
    except Exception as e:
        _cleanup()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating custom voice: {str(e)}"
        )


@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str = "ru",
):
    """
    Транскрибировать аудио через OpenAI Whisper.
    Принимает MP3/WAV/M4A/WebM, возвращает текст.
    Используется для добавления голосовых воспоминаний.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured"
        )

    # Допустимые форматы Whisper
    allowed_audio = {"mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg"}
    suffix = Path(audio_file.filename or "audio.webm").suffix.lstrip(".").lower()
    if not suffix:
        suffix = "webm"

    contents = await audio_file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пустой аудиофайл"
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
            )

        return {"text": transcript.text, "language": language}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка транскрипции: {str(e)}"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/family/sync-memories/{memorial_id}")
async def sync_family_memories_endpoint(
    memorial_id: int,
    dry_run: bool = False,
    db: Session = Depends(get_db),
):
    """
    Memory Sync Agent: находит упоминания родственников в воспоминаниях мемориала
    и создаёт "отражённые" воспоминания (source="family_sync") в мемориалах родственников.

    dry_run=true — только анализирует, не записывает в БД.
    """
    try:
        result = await sync_family_memories(memorial_id=memorial_id, db=db, dry_run=dry_run)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка синхронизации: {str(e)}"
        )


@router.post("/avatar/live", response_model=LiveSessionStartResponse)
async def start_live_avatar_session(
    request: LiveSessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a live avatar video session (Pro / Lifetime Pro only).

    Pro plan:        deducts from monthly counter (UserUsage.live_sessions).
    Lifetime Pro:    deducts from pre-paid pool (User.live_sessions_remaining).

    The endpoint gates the session with billing checks and records usage.
    Actual live video infrastructure (WebRTC / D-ID Live) must be integrated separately.
    Returns a session_id that the client uses to initiate the video stream.
    """
    memorial = db.query(Memorial).filter(Memorial.id == request.memorial_id).first()
    if not memorial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memorial not found")

    check_live_session_quota(current_user, db)
    increment_live_session_usage(current_user, db)

    # Build usage info for the response
    db.refresh(current_user)
    limits = get_limits(current_user)
    plan = _effective_plan(current_user)
    uses_pool = limits.get("live_session_pool", False)

    from app.services.billing import _get_or_create_usage
    usage = _get_or_create_usage(current_user.id, db)

    session_id = uuid.uuid4().hex

    if uses_pool:
        return LiveSessionStartResponse(
            session_id=session_id,
            memorial_id=request.memorial_id,
            sessions_used=0,
            sessions_limit=None,
            sessions_remaining=current_user.live_sessions_remaining,
            message=(
                f"Live avatar session started. "
                f"{current_user.live_sessions_remaining} session(s) remaining in your pool."
            ),
        )

    monthly_limit = limits.get("live_sessions_per_month", 0)
    return LiveSessionStartResponse(
        session_id=session_id,
        memorial_id=request.memorial_id,
        sessions_used=usage.live_sessions,
        sessions_limit=monthly_limit,
        sessions_remaining=max(0, monthly_limit - usage.live_sessions),
        message=(
            f"Live avatar session started. "
            f"Used {usage.live_sessions}/{monthly_limit} sessions this month (plan: {plan})."
        ),
    )


@router.get("/elevenlabs/quota", response_model=ElevenLabsQuotaResponse)
async def get_elevenlabs_quota(_current_user: User = Depends(get_current_user)):
    """
    Остаток символов TTS по подписке ElevenLabs (для отображения в UI чата).
    """
    key = (settings.ELEVENLABS_API_KEY or "").strip()
    if not key:
        return ElevenLabsQuotaResponse(
            configured=False,
            tier=None,
            character_count=0,
            character_limit=0,
            characters_remaining=0,
            next_character_count_reset_unix=None,
        )
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": key},
                timeout=12.0,
            )
        if r.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ElevenLabs API returned {r.status_code}",
            )
        data = r.json()
        used = int(data.get("character_count") or 0)
        limit = int(data.get("character_limit") or 0)
        remaining = max(0, limit - used) if limit else 0
        return ElevenLabsQuotaResponse(
            configured=True,
            tier=data.get("tier"),
            character_count=used,
            character_limit=limit,
            characters_remaining=remaining,
            next_character_count_reset_unix=data.get("next_character_count_reset_unix"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
