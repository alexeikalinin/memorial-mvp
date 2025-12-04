"""
API endpoints для работы с S3 (presigned URLs).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
from pathlib import Path

from app.db import get_db
from app.models import Memorial
from app.schemas import PresignedUploadUrlRequest, PresignedUploadUrlResponse
from app.services.s3_service import get_presigned_upload_url
from app.config import settings

router = APIRouter(prefix="/s3", tags=["s3"])


@router.post("/presigned-upload-url", response_model=PresignedUploadUrlResponse)
async def get_presigned_upload_url_endpoint(
    request: PresignedUploadUrlRequest,
    memorial_id: int = Query(..., description="ID мемориала"),
    db: Session = Depends(get_db),
):
    """
    Получить presigned URL для прямой загрузки файла в S3.
    
    Клиент может использовать этот URL для загрузки файла напрямую в S3,
    минуя backend сервер.
    
    Query параметры:
    - memorial_id: ID мемориала, к которому относится файл
    """
    if not settings.USE_S3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="S3 is not enabled. Set USE_S3=true in configuration."
        )
    
    # Проверка существования мемориала
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    # Проверка размера файла
    if request.file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Генерация уникального ключа S3
    file_id = str(uuid.uuid4())
    file_ext = Path(request.file_name).suffix
    s3_key = f"memorials/{memorial_id}/{file_id}{file_ext}"
    
    # Генерация presigned URL
    upload_url = get_presigned_upload_url(
        s3_key=s3_key,
        content_type=request.content_type,
        expires_in=3600  # 1 час
    )
    
    if not upload_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate presigned URL"
        )
    
    return PresignedUploadUrlResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=3600
    )

