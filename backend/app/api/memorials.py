"""
API endpoints для работы с мемориалами, медиа и воспоминаниями.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
from pathlib import Path
from datetime import datetime, timezone

from app.auth import get_current_user, get_optional_user, require_memorial_access
from app.db import get_db
from app.models import Memorial, Media, Memory, MediaType, MemorialAccess, MemorialInvite, User, UserRole
from app.schemas import (
    MemorialCreate,
    MemorialResponse,
    MemorialDetailResponse,
    MemorialListItem,
    MemorialUpdate,
    MediaResponse,
    MemoryCreate,
    MemoryResponse,
    MemoryUpdate,
    SetCoverRequest,
    TimelineItem,
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
    get_public_url,
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


@router.get("/", response_model=List[MemorialListItem])
async def list_memorials(
    language: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить список мемориалов, к которым у текущего пользователя есть доступ.
    """
    # Subquery counts — один запрос вместо N*2
    memories_count_sq = (
        db.query(Memory.memorial_id, func.count(Memory.id).label("cnt"))
        .group_by(Memory.memorial_id)
        .subquery()
    )
    media_count_sq = (
        db.query(Media.memorial_id, func.count(Media.id).label("cnt"))
        .group_by(Media.memorial_id)
        .subquery()
    )
    # Показываем все мемориалы: свои (через MemorialAccess) + все публичные
    accessible_ids = (
        db.query(MemorialAccess.memorial_id)
        .filter(MemorialAccess.user_id == current_user.id)
        .subquery()
    )
    rows = (
        db.query(
            Memorial,
            func.coalesce(memories_count_sq.c.cnt, 0).label("memories_count"),
            func.coalesce(media_count_sq.c.cnt, 0).label("media_count"),
        )
        .outerjoin(memories_count_sq, Memorial.id == memories_count_sq.c.memorial_id)
        .outerjoin(media_count_sq, Memorial.id == media_count_sq.c.memorial_id)
        .filter(
            (Memorial.is_public == True) | (Memorial.id.in_(accessible_ids))
        )
        .filter(Memorial.language == language if language else True)
        .order_by(Memorial.created_at.desc())
        .all()
    )
    # Подтягиваем file_url для обложек одним запросом
    cover_ids = [m.cover_photo_id for m, _, _ in rows if m.cover_photo_id]
    cover_urls: dict[int, str] = {}
    if cover_ids:
        media_rows = db.query(Media.id, Media.file_url).filter(Media.id.in_(cover_ids)).all()
        cover_urls = {mid: url for mid, url in media_rows if url}

    return [
        MemorialListItem(
            id=m.id,
            name=m.name,
            description=m.description,
            birth_date=m.birth_date,
            death_date=m.death_date,
            is_public=m.is_public,
            cover_photo_id=m.cover_photo_id,
            cover_photo_url=cover_urls.get(m.cover_photo_id) if m.cover_photo_id else None,
            memories_count=mc,
            media_count=mc2,
            language=getattr(m, "language", "ru"),
            created_at=m.created_at,
        )
        for m, mc, mc2 in rows
    ]


@router.post("/", response_model=MemorialResponse, status_code=status.HTTP_201_CREATED)
async def create_memorial(
    memorial: MemorialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создать новый мемориал. Текущий пользователь автоматически получает роль OWNER.
    """
    db_memorial = Memorial(**memorial.dict(), owner_id=current_user.id)
    db.add(db_memorial)
    db.flush()  # получаем id до commit
    access = MemorialAccess(
        memorial_id=db_memorial.id,
        user_id=current_user.id,
        role=UserRole.OWNER,
    )
    db.add(access)
    db.commit()
    db.refresh(db_memorial)
    return db_memorial


@router.get("/{memorial_id}", response_model=MemorialDetailResponse)
async def get_memorial(
    memorial_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Получить мемориал по ID со всеми медиа и воспоминаниями.
    Публичные мемориалы доступны без авторизации.
    """
    require_memorial_access(memorial_id, current_user, db, allow_public=True)

    memorial = (
        db.query(Memorial)
        .options(joinedload(Memorial.media), joinedload(Memorial.memories))
        .filter(Memorial.id == memorial_id)
        .first()
    )

    # Определяем роль текущего пользователя
    current_user_role = None
    if current_user:
        access = db.query(MemorialAccess).filter(
            MemorialAccess.memorial_id == memorial_id,
            MemorialAccess.user_id == current_user.id,
        ).first()
        if access:
            current_user_role = access.role.value

    response = MemorialDetailResponse.model_validate(memorial)
    response.current_user_role = current_user_role
    return response


@router.delete("/{memorial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memorial(
    memorial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удалить мемориал и все связанные данные (медиа, воспоминания, embeddings).
    Только OWNER может удалить мемориал.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.OWNER)

    # Удаляем медиафайлы с диска
    for media in memorial.media:
        try:
            if media.file_path and not settings.USE_S3:
                file_path = Path(media.file_path)
                if file_path.exists():
                    file_path.unlink()
            if media.thumbnail_path:
                thumb_path = Path(media.thumbnail_path)
                if thumb_path.exists():
                    thumb_path.unlink()
        except Exception as e:
            print(f"Warning: Error deleting media file: {e}")

    # Удаляем embeddings из векторной БД
    for memory in memorial.memories:
        if memory.embedding_id:
            try:
                from app.services.ai_tasks import delete_memory_embedding
                import asyncio
                asyncio.run(delete_memory_embedding(memory.id, memorial_id))
            except Exception as e:
                print(f"Warning: Error deleting embedding for memory {memory.id}: {e}")

    db.delete(memorial)
    db.commit()
    return None


@router.get("/{memorial_id}/qr")
async def get_qr_code(
    memorial_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Получить QR-код для публичной страницы мемориала (PNG).
    """
    from io import BytesIO
    try:
        import qrcode
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QR code library not installed. Run: pip install 'qrcode[pil]'"
        )

    memorial = require_memorial_access(memorial_id, current_user, db, allow_public=True)

    frontend_url = settings.PUBLIC_FRONTEND_URL.rstrip("/")
    url = f"{frontend_url}/m/{memorial_id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=memorial_{memorial_id}_qr.png"},
    )


@router.patch("/{memorial_id}", response_model=MemorialResponse)
async def update_memorial(
    memorial_id: int,
    memorial_update: MemorialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновить мемориал. Требуется роль EDITOR или выше.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    
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
    current_user: User = Depends(get_current_user),
):
    """
    Загрузить медиа-файл для мемориала. Требуется роль EDITOR или выше.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    
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
        
        # Загрузка в S3 / Supabase Storage если настроено
        file_url = None
        s3_key = None
        s3_thumbnail_key = None
        if settings.USE_S3:
            s3_key = f"memorials/{memorial_id}/{file_name}"
            if upload_file_to_s3(file_path, s3_key, file.content_type):
                # Supabase Storage: используем публичный URL; AWS S3: presigned URL
                if settings.supabase_public_url:
                    file_url = get_public_url(s3_key)
                else:
                    file_url = get_presigned_download_url(s3_key, expires_in=86400 * 365)
                file_path.unlink(missing_ok=True)  # удаляем локальную копию

            # Загрузка thumbnail в S3
            if thumbnail_path:
                thumb_local = Path(thumbnail_path)
                if thumb_local.exists():
                    s3_thumbnail_key = f"memorials/{memorial_id}/thumbnails/{thumb_local.name}"
                    if upload_file_to_s3(thumb_local, s3_thumbnail_key, "image/jpeg"):
                        thumb_local.unlink(missing_ok=True)

        # Создание записи в БД
        db_media = Media(
            memorial_id=memorial_id,
            file_path=s3_key if settings.USE_S3 and s3_key else str(file_path),
            file_url=file_url,
            file_name=file.filename,
            file_size=len(contents),
            mime_type=file.content_type,
            media_type=media_type,
            thumbnail_path=s3_thumbnail_key if settings.USE_S3 and s3_thumbnail_key else thumbnail_path,
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
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Получить все медиа-файлы мемориала. Публичные мемориалы доступны без авторизации.
    """
    require_memorial_access(memorial_id, current_user, db, allow_public=True)
    return db.query(Media).filter(Media.memorial_id == memorial_id).all()


@router.delete("/{memorial_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    memorial_id: int,
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удалить медиа-файл мемориала. Требуется роль EDITOR или выше.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    
    # Проверка существования медиа
    media = db.query(Media).filter(
        Media.id == media_id,
        Media.memorial_id == memorial_id
    ).first()
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Удаление файлов с диска
    try:
        # Удаление основного файла
        if media.file_path and not settings.USE_S3:
            file_path = Path(media.file_path)
            if file_path.exists():
                file_path.unlink()
                print(f"✅ Deleted main file: {file_path}")
        
        # Удаление миниатюр (если есть)
        if media.thumbnail_path:
            thumbnail_path = Path(media.thumbnail_path)
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                print(f"✅ Deleted thumbnail: {thumbnail_path}")
        
        # Удаление всех миниатюр для фото (small, medium, large)
        if media.media_type == MediaType.PHOTO:
            file_path = Path(media.file_path)
            for size in ["small", "medium", "large"]:
                thumbnail_path = THUMBNAILS_DIR / f"{file_path.stem}_{size}.jpg"
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                    print(f"✅ Deleted thumbnail {size}: {thumbnail_path}")
        
        # Удаление анимированного видео (если есть)
        if media.is_animated and media.file_url:
            # Если это анимированное фото, оригинальный файл может быть заменен видео
            # Проверяем, есть ли видео-файл
            if media.file_path and not settings.USE_S3:
                video_path = Path(media.file_path)
                if video_path.exists() and video_path.suffix in ['.mp4', '.mov', '.webm']:
                    video_path.unlink()
                    print(f"✅ Deleted animated video: {video_path}")
        
        # Удаление из S3 если используется
        if settings.USE_S3 and media.file_path:
            try:
                from app.services.s3_service import delete_file_from_s3
                delete_file_from_s3(media.file_path)
                print(f"✅ Deleted file from S3: {media.file_path}")
            except Exception as s3_error:
                print(f"⚠️  Warning: Failed to delete from S3: {s3_error}")
        
    except Exception as file_error:
        print(f"⚠️  Warning: Error deleting files: {file_error}")
        # Продолжаем удаление записи из БД даже если файлы не удалились
    
    # Удаление записи из БД
    db.delete(media)
    db.commit()
    
    print(f"✅ Deleted media {media_id} from memorial {memorial_id}")
    return None


@router.post("/{memorial_id}/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memorial_id: int,
    memory: MemoryCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
    invite_token: Optional[str] = Query(None, description="Инвайт-токен для анонимного вклада"),
):
    """
    Добавить текстовое воспоминание к мемориалу.
    Доступно авторизованным пользователям (EDITOR+) или держателям invite_token.
    """
    if invite_token:
        invite = db.query(MemorialInvite).filter(MemorialInvite.token == invite_token).first()
        if not invite or invite.memorial_id != memorial_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid invite token")
        if invite.expires_at and invite.expires_at.replace(tzinfo=None) < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invite token expired")
        if not invite.permissions.get("add_memories"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invite does not allow adding memories")
        memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
        if not memorial:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memorial not found")
    elif current_user:
        memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    
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

    # Инвалидируем кэш персоны аватара — воспоминания изменились
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.delete(f"persona:{memorial_id}")
        r.close()
    except Exception:
        pass  # Redis недоступен — кэш истечёт сам по TTL

    return db_memory


@router.patch("/{memorial_id}/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memorial_id: int,
    memory_id: int,
    memory_update: MemoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновить воспоминание. Требуется роль EDITOR или выше.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    
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
    current_user: User = Depends(get_current_user),
):
    """
    Удалить воспоминание. Требуется роль EDITOR или выше.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)
    
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
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Получить воспоминания мемориала. Публичные мемориалы доступны без авторизации.
    """
    require_memorial_access(memorial_id, current_user, db, allow_public=True)
    query = db.query(Memory).filter(Memory.memorial_id == memorial_id)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(Memory.title.ilike(pattern), Memory.content.ilike(pattern))
        )
    return query.all()


@router.patch("/{memorial_id}/cover", response_model=MemorialResponse)
async def set_cover_photo(
    memorial_id: int,
    body: SetCoverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Установить фото обложки мемориала. Требуется роль EDITOR или выше.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)

    if body.media_id is not None:
        media = db.query(Media).filter(
            Media.id == body.media_id,
            Media.memorial_id == memorial_id,
        ).first()
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found in this memorial"
            )

    memorial.cover_photo_id = body.media_id
    db.commit()
    db.refresh(memorial)
    return memorial


_MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
_MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _month_year_label(dt: datetime, lang: str) -> str:
    if lang == "en":
        return f"{_MONTHS_EN[dt.month - 1]} {dt.year}"
    return f"{_MONTHS_RU[dt.month - 1]} {dt.year}"


@router.get("/{memorial_id}/timeline", response_model=List[TimelineItem])
async def get_timeline(
    memorial_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Хронологическая лента воспоминаний. Публичные мемориалы доступны без авторизации.
    Сначала события с датой (по event_date), затем без даты (по дате добавления).
    """
    memorial = require_memorial_access(memorial_id, current_user, db, allow_public=True)

    lang = (memorial.language or "ru").lower()
    if lang not in ("en", "ru"):
        lang = "ru"
    undated_label = "No date" if lang == "en" else "Без даты"

    dated = (
        db.query(Memory)
        .filter(Memory.memorial_id == memorial_id, Memory.event_date.isnot(None))
        .order_by(Memory.event_date)
        .all()
    )
    undated = (
        db.query(Memory)
        .filter(Memory.memorial_id == memorial_id, Memory.event_date.is_(None))
        .order_by(Memory.created_at)
        .all()
    )

    items = []
    for m in dated:
        items.append(
            TimelineItem(
                id=m.id,
                year=m.event_date.year,
                date_label=_month_year_label(m.event_date, lang),
                type="memory",
                title=m.title,
                content=m.content,
                event_date=m.event_date,
            )
        )
    for m in undated:
        ca = m.created_at
        year = ca.year if ca else 0
        items.append(
            TimelineItem(
                id=m.id,
                year=year,
                date_label=undated_label,
                type="memory",
                title=m.title,
                content=m.content,
                event_date=None,
            )
        )
    return items

