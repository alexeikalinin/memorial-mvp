"""
API endpoints для работы с мемориалами, медиа и воспоминаниями.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from app.db import get_db
from app.models import Memorial, Media, Memory, MediaType
from app.schemas import (
    MemorialCreate,
    MemorialResponse,
    MemorialDetailResponse,
    MemorialUpdate,
    MediaResponse,
    MemoryCreate,
    MemoryResponse,
    MemoryUpdate,
)
from app.config import settings
from app.services.media_service import (
    generate_all_thumbnails,
    validate_image_file,
    get_image_dimensions,
    optimize_image,
    is_image_file,
)
from app.services.video_service import (
    validate_video_file,
    get_video_info,
    generate_video_thumbnail,
    is_video_file,
)
from app.services.s3_service import (
    upload_file_to_s3,
    get_presigned_upload_url,
    get_presigned_download_url,
)

router = APIRouter(prefix="/memorials", tags=["memorials"])

# Создание директорий для загрузок
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
THUMBNAILS_DIR = UPLOAD_DIR / "thumbnails"
THUMBNAILS_DIR.mkdir(exist_ok=True)


def get_media_type_from_mime(mime_type: str) -> MediaType:
    """Определяет тип медиа по MIME типу."""
    if mime_type.startswith("image/"):
        return MediaType.PHOTO
    elif mime_type.startswith("video/"):
        return MediaType.VIDEO
    elif mime_type.startswith("audio/"):
        return MediaType.AUDIO
    else:
        return MediaType.DOCUMENT


@router.post("/", response_model=MemorialResponse, status_code=status.HTTP_201_CREATED)
async def create_memorial(
    memorial: MemorialCreate,
    db: Session = Depends(get_db),
    # TODO: Добавить аутентификацию и получать owner_id из токена
    owner_id: int = 1,  # Заглушка для MVP
):
    """
    Создать новый мемориал.
    """
    db_memorial = Memorial(**memorial.dict(), owner_id=owner_id)
    db.add(db_memorial)
    db.commit()
    db.refresh(db_memorial)
    return db_memorial


@router.get("/{memorial_id}", response_model=MemorialDetailResponse)
async def get_memorial(
    memorial_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить мемориал по ID со всеми медиа и воспоминаниями.
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    return memorial


@router.patch("/{memorial_id}", response_model=MemorialResponse)
async def update_memorial(
    memorial_id: int,
    memorial_update: MemorialUpdate,
    db: Session = Depends(get_db),
    # TODO: Добавить проверку прав доступа
):
    """
    Обновить мемориал.
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    update_data = memorial_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(memorial, field, value)
    
    db.commit()
    db.refresh(memorial)
    return memorial


@router.post("/{memorial_id}/media/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    memorial_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Загрузить медиа-файл для мемориала.
    Сохраняет файл локально (или возвращает presigned S3 URL в будущем).
    """
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    # Проверка расширения файла
    file_ext = Path(file.filename).suffix[1:].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{file_ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Генерация уникального имени файла
    file_id = str(uuid.uuid4())
    file_name = f"{file_id}_{file.filename}"
    file_path = UPLOAD_DIR / file_name
    
    # Сохранение файла
    try:
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Определение типа медиа
        media_type = get_media_type_from_mime(file.content_type or "application/octet-stream")
        
        # Обработка медиа: валидация, оптимизация, генерация миниатюр/превью
        thumbnail_path = None
        if media_type == MediaType.PHOTO:
            # Валидация изображения
            is_valid, error_msg = validate_image_file(file_path)
            if not is_valid:
                file_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid image file: {error_msg}"
                )
            
            # Оптимизация больших изображений (если больше 5MB)
            if len(contents) > 5 * 1024 * 1024:  # 5MB
                optimize_image(file_path, max_size=(1920, 1920), quality=85)
                # Обновляем размер после оптимизации
                contents = file_path.read_bytes()
            
            # Генерация миниатюр
            thumbnails = generate_all_thumbnails(file_path, THUMBNAILS_DIR)
            if thumbnails.get("medium"):
                thumbnail_path = thumbnails["medium"]
        
        elif media_type == MediaType.VIDEO:
            # Валидация видео
            is_valid, error_msg = validate_video_file(file_path)
            if not is_valid:
                file_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid video file: {error_msg}"
                )
            
            # Генерация превью для видео
            video_preview_path = THUMBNAILS_DIR / f"{file_path.stem}_preview.jpg"
            if generate_video_thumbnail(file_path, video_preview_path, time_offset=1.0):
                thumbnail_path = str(video_preview_path)
        
        # Загрузка в S3 если настроено
        file_url = None
        s3_key = None
        if settings.USE_S3:
            s3_key = f"memorials/{memorial_id}/{file_name}"
            if upload_file_to_s3(file_path, s3_key, file.content_type):
                file_url = get_presigned_download_url(s3_key, expires_in=86400 * 365)  # 1 год
                # Опционально: удалить локальный файл после загрузки в S3
                # file_path.unlink()
        
        # Создание записи в БД
        db_media = Media(
            memorial_id=memorial_id,
            file_path=str(file_path) if not settings.USE_S3 else s3_key or str(file_path),
            file_url=file_url,
            file_name=file.filename,
            file_size=len(contents),
            mime_type=file.content_type,
            media_type=media_type,
            thumbnail_path=thumbnail_path,
        )
        db.add(db_media)
        db.commit()
        db.refresh(db_media)
        
        return db_media
    
    except Exception as e:
        # Удаление файла при ошибке
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("/{memorial_id}/media", response_model=List[MediaResponse])
async def get_memorial_media(
    memorial_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить все медиа-файлы мемориала.
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    return memorial.media


@router.post("/{memorial_id}/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memorial_id: int,
    memory: MemoryCreate,
    db: Session = Depends(get_db),
):
    """
    Добавить текстовое воспоминание к мемориалу.
    """
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    db_memory = Memory(
        **memory.dict(),
        memorial_id=memorial_id,
        source="user"
    )
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    
    # Создание embedding в фоновой задаче или синхронно
    try:
        from app.workers.worker import create_memory_embedding_task
        create_memory_embedding_task.delay(
            memory_id=db_memory.id,
            memorial_id=memorial_id,
            text=db_memory.content
        )
    except Exception as e:
        # Если worker недоступен, создаем embedding синхронно
        error_msg = str(e)
        if "Connection refused" in error_msg or "redis" in error_msg.lower() or "OperationalError" in error_msg:
            try:
                # Синхронное создание embedding
                import asyncio
                from app.services.ai_tasks import get_embedding, upsert_memory_embedding
                
                async def create_embedding_sync():
                    embedding = await get_embedding(db_memory.content)
                    vector_id = await upsert_memory_embedding(
                        memory_id=db_memory.id,
                        memorial_id=memorial_id,
                        text=db_memory.content,
                        embedding=embedding,
                        title=db_memory.title
                    )
                    db_memory.embedding_id = vector_id
                    db.commit()
                
                asyncio.run(create_embedding_sync())
                print(f"Created embedding synchronously for memory {db_memory.id}")
            except Exception as sync_error:
                print(f"Warning: Failed to create embedding synchronously: {sync_error}")
        else:
            print(f"Warning: Failed to queue embedding task: {e}")
    
    return db_memory


@router.patch("/{memorial_id}/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memorial_id: int,
    memory_id: int,
    memory_update: MemoryUpdate,
    db: Session = Depends(get_db),
):
    """
    Обновить воспоминание.
    При изменении текста пересоздается embedding.
    """
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    # Проверка существования воспоминания
    db_memory = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.memorial_id == memorial_id
    ).first()
    if not db_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Сохраняем старый контент для проверки изменений
    old_content = db_memory.content
    content_changed = False
    
    # Обновляем только переданные поля
    update_data = memory_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "content" and value != old_content:
            content_changed = True
        setattr(db_memory, field, value)
    
    db.commit()
    db.refresh(db_memory)
    
    # Если изменился контент, пересоздаем embedding
    if content_changed:
        try:
            from app.workers.worker import create_memory_embedding_task
            # Удаляем старый embedding
            if db_memory.embedding_id:
                from app.services.ai_tasks import delete_memory_embedding
                import asyncio
                asyncio.run(delete_memory_embedding(memory_id, memorial_id))
            
            # Создаем новый embedding
            create_memory_embedding_task.delay(
                memory_id=db_memory.id,
                memorial_id=memorial_id,
                text=db_memory.content
            )
        except Exception as e:
            # Если worker недоступен, создаем синхронно
            error_msg = str(e)
            if "Connection refused" in error_msg or "redis" in error_msg.lower():
                try:
                    import asyncio
                    from app.services.ai_tasks import get_embedding, upsert_memory_embedding
                    
                    async def recreate_embedding():
                        embedding = await get_embedding(db_memory.content)
                        vector_id = await upsert_memory_embedding(
                            memory_id=db_memory.id,
                            memorial_id=memorial_id,
                            text=db_memory.content,
                            embedding=embedding,
                            title=db_memory.title
                        )
                        db_memory.embedding_id = vector_id
                        db.commit()
                    
                    asyncio.run(recreate_embedding())
                except Exception as sync_error:
                    print(f"Warning: Failed to recreate embedding: {sync_error}")
    
    return db_memory


@router.delete("/{memorial_id}/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memorial_id: int,
    memory_id: int,
    db: Session = Depends(get_db),
):
    """
    Удалить воспоминание.
    Также удаляется соответствующий embedding из векторной БД.
    """
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    # Проверка существования воспоминания
    db_memory = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.memorial_id == memorial_id
    ).first()
    if not db_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Удаляем embedding из векторной БД
    if db_memory.embedding_id:
        try:
            from app.services.ai_tasks import delete_memory_embedding
            import asyncio
            asyncio.run(delete_memory_embedding(memory_id, memorial_id))
        except Exception as e:
            print(f"Warning: Failed to delete embedding: {e}")
    
    # Удаляем воспоминание
    db.delete(db_memory)
    db.commit()
    
    return None


@router.get("/{memorial_id}/memories", response_model=List[MemoryResponse])
async def get_memorial_memories(
    memorial_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить все воспоминания мемориала.
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    return memorial.memories

