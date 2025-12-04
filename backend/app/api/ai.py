"""
API endpoints для AI-функций: анимация фото и чат с аватаром.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path

from app.db import get_db
from app.models import Memorial, Media, Memory, MediaType
from app.schemas import (
    PhotoAnimateRequest,
    PhotoAnimateResponse,
    AvatarChatRequest,
    AvatarChatResponse,
    AnimationStatusRequest,
    AnimationStatusResponse,
)
from app.services.ai_tasks import (
    get_embedding,
    generate_rag_response,
    search_similar_memories,
    generate_speech_elevenlabs,
    create_custom_voice_elevenlabs,
    animate_photo,
    get_animation_status,
)
from app.workers.worker import animate_photo_task, create_memory_embedding_task
from app.config import settings
import os
import uuid

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/photo/animate", response_model=PhotoAnimateResponse)
async def animate_photo(
    request: PhotoAnimateRequest,
    db: Session = Depends(get_db),
):
    """
    Запустить задачу оживления фото через D-ID или HeyGen.
    Задача выполняется в фоновом режиме через Celery worker.
    """
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
    
    # Получение публичного URL изображения
    # В production это должен быть S3 URL
    if settings.USE_S3 and media.file_url:
        image_url = media.file_url
    else:
        # Для локальной разработки - используем API endpoint для получения медиа
        # ВАЖНО: D-ID требует, чтобы URL заканчивался на .jpg, .jpeg или .png
        # Поэтому добавляем расширение файла к URL
        public_api_url = getattr(settings, 'PUBLIC_API_URL', None)
        
        # Определяем расширение файла из file_name
        file_extension = ""
        if media.file_name:
            # Извлекаем расширение из имени файла
            if '.' in media.file_name:
                file_extension = "." + media.file_name.rsplit('.', 1)[1].lower()
                # Проверяем, что это валидное расширение для изображения
                if file_extension not in ['.jpg', '.jpeg', '.png']:
                    file_extension = '.jpg'  # Fallback на .jpg
            else:
                file_extension = '.jpg'  # Fallback на .jpg
        else:
            file_extension = '.jpg'  # Fallback на .jpg
        
        if public_api_url:
            # Используем PUBLIC_API_URL с расширением файла
            image_url = f"{public_api_url}/api/v1/media/{media.id}{file_extension}"
        else:
            # Fallback на localhost (не будет работать с внешними сервисами, но для тестирования)
            image_url = f"http://localhost:8000/api/v1/media/{media.id}{file_extension}"
            print(f"⚠️ WARNING: Using localhost URL for image. External services require a public URL!")
            print(f"   Set PUBLIC_API_URL in .env (e.g., https://your-ngrok-url.ngrok.io) or use S3")
        print(f"Using API endpoint for image: {image_url}")
    
    # Запуск фоновой задачи
    try:
        task = animate_photo_task.delay(
            media_id=request.media_id,
            image_url=image_url,
            script=request.prompt
        )
        
        provider = "heygen" if settings.USE_HEYGEN else "d-id"
        
        return PhotoAnimateResponse(
            task_id=task.id,
            status="pending",
            provider=provider,
            message=f"Animation task started with {provider}. Check status later."
        )
    except Exception as e:
        # Обработка ошибок Redis/Celery
        error_msg = str(e)
        if "Connection refused" in error_msg or "redis" in error_msg.lower() or "OperationalError" in error_msg:
            # Fallback: попытка синхронного выполнения (не рекомендуется для production)
            # Для MVP можно использовать, но лучше запустить Redis
            try:
                # Прямой вызов функции анимации (синхронно)
                from app.services.ai_tasks import animate_photo
                import asyncio
                
                result = asyncio.run(animate_photo(image_url, request.prompt))
                provider = result.get("provider", "heygen" if settings.USE_HEYGEN else "d-id")
                task_id = result.get("task_id")
                
                # Сохраняем task_id в БД
                media.animation_task_id = task_id
                db.commit()
                
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
    
    # Получаем все воспоминания (не только с embeddings)
    all_memories = db.query(Memory).filter(
        Memory.memorial_id == request.memorial_id
    ).all()
    
    if not all_memories:
        return AvatarChatResponse(
            answer="У меня пока нет информации об этом человеке. Пожалуйста, добавьте воспоминания, чтобы я мог отвечать на вопросы.",
            sources=[]
        )
    
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
    
    if not memories:
        # Если все еще нет воспоминаний с embeddings, возвращаем более информативное сообщение
        total_count = len(all_memories)
        without_embeddings = len(all_memories) - len(memories_with_embeddings)
        error_msg = f"Воспоминания добавлены ({total_count}), но embeddings еще не созданы ({without_embeddings} без embeddings)."
        if without_embeddings > 0:
            error_msg += " Пожалуйста, подождите несколько секунд и попробуйте снова. Если проблема сохраняется, проверьте логи сервера."
        return AvatarChatResponse(
            answer=error_msg,
            sources=[]
        )
    
    try:
        # Создание embedding вопроса
        question_embedding = await get_embedding(request.question)
        
        # Поиск релевантных воспоминаний в векторной БД
        # Понижаем порог для лучшего поиска, особенно для общих вопросов
        similar_memories = await search_similar_memories(
            memorial_id=request.memorial_id,
            query_embedding=question_embedding,
            top_k=5,
            min_score=0.2  # Еще более понижен порог для общих вопросов
        )
        
        print(f"🔍 Found {len(similar_memories)} similar memories for question: '{request.question}'")
        for i, mem in enumerate(similar_memories):
            print(f"  {i+1}. Memory ID: {mem.get('memory_id')}, Score: {mem.get('score', 0):.3f}, Title: {mem.get('title', 'N/A')}")
        
        if not similar_memories:
            print(f"⚠️ No similar memories found for question: '{request.question}'")
            return AvatarChatResponse(
                answer="У меня нет информации на эту тему.",
                sources=[]
            )
        
        # ВАЖНО: Всегда получаем полный текст из БД, так как в векторной БД
        # текст может быть обрезанным (например, только 1000 символов в Qdrant payload)
        context_chunks = []
        for mem in similar_memories:
            memory_id = mem.get("memory_id")
            if memory_id:
                # Всегда получаем полный текст из БД для гарантии полноты контекста
                memory = db.query(Memory).filter(Memory.id == memory_id).first()
                if memory:
                    context_chunks.append({
                        "text": memory.content,  # Полный текст из БД
                        "memory_id": memory.id,
                        "score": mem.get("score", 0),
                        "title": memory.title
                    })
                    print(f"✅ Added context chunk: Memory #{memory.id}, text length: {len(memory.content)} chars")
                else:
                    print(f"⚠️ Memory {memory_id} not found in database")
            elif mem.get("text"):
                # Fallback: если memory_id нет, используем текст из payload
                # (но это не должно происходить в нормальной работе)
                context_chunks.append(mem)
                print(f"⚠️ Using text from payload (no memory_id): {len(mem.get('text', ''))} chars")
        
        if not context_chunks:
            print(f"❌ No context chunks created from {len(similar_memories)} similar memories")
            return AvatarChatResponse(
                answer="У меня нет информации на эту тему.",
                sources=[]
            )
        
        print(f"📝 Created {len(context_chunks)} context chunks for RAG")
        
        # Генерация ответа через OpenAI с улучшенным RAG
        answer, source_ids = await generate_rag_response(
            question=request.question,
            context_chunks=context_chunks,
            memorial_name=memorial.name
        )
        
        # Формируем читаемые источники
        sources = []
        for chunk in context_chunks:
            memory_id = chunk.get("memory_id")
            title = chunk.get("title", "")
            if memory_id:
                source_text = f"Воспоминание #{memory_id}"
                if title:
                    source_text += f": {title}"
                sources.append(source_text)
        
        # Опциональная генерация аудио
        audio_url = None
        if request.include_audio:
            try:
                # Используем кастомный голос мемориала, если он есть
                voice_id = memorial.voice_id or settings.ELEVENLABS_VOICE_ID
                audio_bytes = await generate_speech_elevenlabs(answer, voice_id=voice_id)
                
                # Сохранение аудио-файла
                audio_dir = Path("uploads/audio")
                audio_dir.mkdir(exist_ok=True)
                audio_filename = f"chat_{request.memorial_id}_{hash(request.question)}.mp3"
                audio_path = audio_dir / audio_filename
                
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)
                
                # В production это должен быть S3 URL
                # Для локальной разработки используем относительный путь (будет работать с frontend)
                if settings.USE_S3:
                    audio_url = f"s3://{settings.S3_BUCKET_NAME}/audio/{audio_filename}"
                else:
                    # Используем относительный путь - frontend добавит базовый URL автоматически
                    audio_url = f"/api/v1/media/audio/{audio_filename}"
            
            except Exception as e:
                # Если генерация аудио не удалась, продолжаем без него
                print(f"Error generating audio: {e}")
        
        return AvatarChatResponse(
            answer=answer,
            audio_url=audio_url,
            sources=sources
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
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
        
        status = status_result.get("status", "unknown")
        error = status_result.get("error")
        
        # Не возвращаем error, если статус processing/pending (это нормально)
        if status in ("processing", "pending") and error:
            error = None
        
        return AnimationStatusResponse(
            task_id=request.task_id,  # Возвращаем оригинальный task_id для совместимости
            status=status,
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


@router.post("/voice/upload")
async def upload_voice(
    memorial_id: int,
    audio_file: UploadFile = File(...),
    voice_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Загрузить аудио-файл с голосом и создать кастомный голос в ElevenLabs.
    
    Требования к аудио:
    - Формат: MP3, WAV, M4A
    - Длительность: минимум 1 минута (рекомендуется)
    - Качество: без посторонних шумов
    """
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    # Проверка формата файла
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file (MP3, WAV, M4A, etc.)"
        )
    
    # Сохранение временного файла
    voice_dir = Path("uploads/voices")
    voice_dir.mkdir(exist_ok=True)
    
    file_extension = Path(audio_file.filename).suffix or ".mp3"
    temp_filename = f"voice_{memorial_id}_{uuid.uuid4().hex}{file_extension}"
    temp_path = voice_dir / temp_filename
    
    try:
        # Сохраняем файл
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Создаем кастомный голос в ElevenLabs
        voice_name_final = voice_name or f"{memorial.name} Voice"
        voice_id = await create_custom_voice_elevenlabs(
            audio_file_path=str(temp_path),
            voice_name=voice_name_final,
            description=f"Custom voice for {memorial.name}"
        )
        
        # Сохраняем voice_id в мемориал
        memorial.voice_id = voice_id
        db.commit()
        db.refresh(memorial)
        
        # Удаляем временный файл
        if temp_path.exists():
            temp_path.unlink()
        
        return {
            "success": True,
            "voice_id": voice_id,
            "voice_name": voice_name_final,
            "message": f"Голос успешно создан и сохранен для мемориала '{memorial.name}'"
        }
    
    except ValueError as e:
        # Удаляем временный файл при ошибке
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Удаляем временный файл при ошибке
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating custom voice: {str(e)}"
        )

