"""
Сервис для работы с AWS S3 (загрузка, получение, presigned URLs).
"""
from typing import Optional
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from app.config import settings
from datetime import timedelta


def get_s3_client():
    """
    Создает и возвращает S3 клиент.
    """
    if not settings.USE_S3:
        return None
    
    if not all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.S3_BUCKET_NAME]):
        return None
    
    return boto3.client(
        's3',
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def upload_file_to_s3(
    local_file_path: Path,
    s3_key: str,
    content_type: Optional[str] = None
) -> bool:
    """
    Загружает файл в S3.
    
    Args:
        local_file_path: Локальный путь к файлу
        s3_key: Ключ (путь) в S3
        content_type: MIME тип файла
    
    Returns:
        True если успешно
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    try:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        s3_client.upload_file(
            str(local_file_path),
            settings.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs=extra_args
        )
        return True
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return False


def get_presigned_upload_url(
    s3_key: str,
    content_type: Optional[str] = None,
    expires_in: int = 3600
) -> Optional[str]:
    """
    Генерирует presigned URL для прямой загрузки файла в S3 из клиента.
    
    Args:
        s3_key: Ключ (путь) в S3
        content_type: MIME тип файла
        expires_in: Время жизни URL в секундах (по умолчанию 1 час)
    
    Returns:
        Presigned URL или None
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    try:
        params = {
            'Bucket': settings.S3_BUCKET_NAME,
            'Key': s3_key,
        }
        
        if content_type:
            params['ContentType'] = content_type
        
        url = s3_client.generate_presigned_url(
            'put_object',
            Params=params,
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None


def get_presigned_download_url(
    s3_key: str,
    expires_in: int = 3600
) -> Optional[str]:
    """
    Генерирует presigned URL для скачивания файла из S3.
    
    Args:
        s3_key: Ключ (путь) в S3
        expires_in: Время жизни URL в секундах (по умолчанию 1 час)
    
    Returns:
        Presigned URL или None
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': s3_key,
            },
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned download URL: {e}")
        return None


def delete_file_from_s3(s3_key: str) -> bool:
    """
    Удаляет файл из S3.
    
    Args:
        s3_key: Ключ (путь) в S3
    
    Returns:
        True если успешно
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    try:
        s3_client.delete_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key
        )
        return True
    except ClientError as e:
        print(f"Error deleting from S3: {e}")
        return False


def file_exists_in_s3(s3_key: str) -> bool:
    """
    Проверяет существование файла в S3.
    
    Args:
        s3_key: Ключ (путь) в S3
    
    Returns:
        True если файл существует
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    try:
        s3_client.head_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key
        )
        return True
    except ClientError:
        return False

