"""
API endpoints для работы с медиа-файлами (получение, статический сервинг).
"""
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
import mimetypes

from app.db import get_db
from app.models import Media
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter(prefix="/media", tags=["media"])

UPLOAD_DIR = Path("uploads")


@router.get("/{media_id_path:path}")  # Используем path для поддержки расширений
async def get_media_file(
    media_id_path: str,  # Может быть "10" или "10.jpg"
    thumbnail: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # Извлекаем media_id из пути (убираем расширение если есть)
    media_id_str = media_id_path.split('.')[0]
    try:
        media_id = int(media_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid media ID"
        )
    """
    Получить медиа-файл по ID.
    
    Query параметры:
    - thumbnail: размер миниатюры (small, medium, large) - только для изображений
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    file_path = Path(media.file_path)
    
    # Если запрашивается миниатюра для изображения
    if thumbnail and media.media_type.value == "photo":
        if thumbnail in ("small", "medium", "large"):
            thumbnail_path = UPLOAD_DIR / "thumbnails" / f"{file_path.stem}_{thumbnail}.jpg"
            if thumbnail_path.exists():
                return FileResponse(
                    thumbnail_path,
                    media_type="image/jpeg",
                    filename=f"{media.file_name}_thumb_{thumbnail}.jpg"
                )
        # Если миниатюра не найдена, возвращаем оригинал
    
    # Проверка существования файла
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found on disk"
        )
    
    # Определение MIME типа
    mime_type = media.mime_type or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    
    return FileResponse(
        file_path,
        media_type=mime_type,
        filename=media.file_name
    )


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Получить аудио-файл по имени файла.
    Используется для обслуживания сгенерированных аудио из чата.
    """
    audio_path = UPLOAD_DIR / "audio" / filename
    
    if not audio_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=filename
    )


@router.get("/{media_id}/info")
async def get_media_info(
    media_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить информацию о медиа-файле (метаданные).
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    file_path = Path(media.file_path)
    file_exists = file_path.exists()
    
    info = {
        "id": media.id,
        "memorial_id": media.memorial_id,
        "file_name": media.file_name,
        "file_size": media.file_size,
        "mime_type": media.mime_type,
        "media_type": media.media_type.value,
        "is_animated": media.is_animated,
        "has_thumbnail": media.thumbnail_path is not None,
        "file_exists": file_exists,
        "created_at": media.created_at.isoformat() if media.created_at else None,
    }
    
    # Добавляем размеры изображения если доступно
    if media.media_type.value == "photo" and file_exists:
        from app.services.media_service import get_image_dimensions
        dimensions = get_image_dimensions(file_path)
        if dimensions:
            info["width"] = dimensions[0]
            info["height"] = dimensions[1]
    
    return info

