"""
Worker для обработки фоновых задач (Celery).
Альтернатива: простой Python скрипт с polling (см. worker_simple.py).
"""
from celery import Celery
from app.config import settings

# Создание Celery приложения
celery_app = Celery(
    "memorial_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="animate_photo", bind=True, max_retries=3)
def animate_photo_task(self, media_id: int, image_url: str, script: str = None):
    """
    Фоновая задача для оживления фото через D-ID или HeyGen.
    
    Args:
        media_id: ID медиа-файла в БД
        image_url: URL изображения
        script: Текст для озвучки
    
    Returns:
        Dict с результатом задачи
    """
    import asyncio
    import httpx
    from app.services.ai_tasks import animate_photo, get_animation_status
    from app.db import SessionLocal
    from app.models import Media, MediaType
    from app.config import settings
    from app.services.s3_service import upload_file_to_s3
    from pathlib import Path
    
    async def process():
        db = SessionLocal()
        try:
            # Получаем медиа
            media = db.query(Media).filter(Media.id == media_id).first()
            if not media:
                return {"status": "error", "message": "Media not found"}
            
            # Запуск анимации через унифицированный интерфейс
            try:
                result = await animate_photo(image_url, script)
                provider = result.get("provider")
                task_id = result.get("task_id")
                
                if not task_id:
                    return {"status": "error", "message": "Failed to start animation"}
                
                # Сохраняем task_id и provider в БД
                media.animation_task_id = task_id
                # TODO: Добавить поле provider в модель Media
                db.commit()
                
                # Ожидание завершения анимации (polling)
                # В production лучше использовать webhook
                max_attempts = 120  # 10 минут при проверке каждые 5 секунд
                for attempt in range(max_attempts):
                    try:
                        status_result = await get_animation_status(provider, task_id)
                        status = status_result.get("status", "").lower()
                        
                        if status in ("done", "completed", "success"):
                            video_url = status_result.get("video_url")
                            if video_url:
                                # Скачиваем видео и сохраняем локально/S3
                                async with httpx.AsyncClient() as client:
                                    video_response = await client.get(video_url, timeout=60.0)
                                    video_response.raise_for_status()
                                    video_data = video_response.content
                                
                                # Сохраняем видео
                                video_filename = f"{Path(media.file_path).stem}_animated.mp4"
                                video_path = Path("uploads") / video_filename
                                video_path.parent.mkdir(exist_ok=True)
                                
                                with open(video_path, "wb") as f:
                                    f.write(video_data)
                                
                                # Загружаем в S3 если настроено
                                if settings.USE_S3:
                                    s3_key = f"memorials/{media.memorial_id}/{video_filename}"
                                    if upload_file_to_s3(video_path, s3_key, "video/mp4"):
                                        video_url = f"s3://{settings.S3_BUCKET_NAME}/{s3_key}"
                                
                                # Обновляем запись в БД
                                media.file_url = video_url
                                media.is_animated = True
                                media.media_type = MediaType.VIDEO
                                media.animation_task_id = None  # Очищаем task_id после завершения
                                db.commit()
                                
                                return {
                                    "status": "completed",
                                    "video_url": video_url,
                                    "provider": provider
                                }
                        
                        elif status in ("error", "failed"):
                            error_msg = status_result.get("error", "Animation failed")
                            return {"status": "error", "message": error_msg, "provider": provider}
                        
                        # Продолжаем ожидание
                        await asyncio.sleep(5)
                    
                    except Exception as e:
                        # При ошибке проверки статуса продолжаем попытки
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(5)
                            continue
                        else:
                            raise
                
                return {"status": "timeout", "message": "Animation took too long", "provider": provider}
            
            except ValueError as e:
                # Ошибка API (недостаточно средств, неверный ключ и т.д.)
                return {"status": "error", "message": str(e)}
            except Exception as e:
                # Другие ошибки - пробуем повторить
                raise self.retry(exc=e, countdown=60)
        
        finally:
            db.close()
    
    return asyncio.run(process())


@celery_app.task(name="create_memory_embedding", bind=True, max_retries=3)
def create_memory_embedding_task(self, memory_id: int, memorial_id: int, text: str):
    """
    Фоновая задача для создания embedding воспоминания и сохранения в Pinecone.
    """
    import asyncio
    from app.services.ai_tasks import get_embedding, upsert_memory_embedding
    from app.db import SessionLocal
    from app.models import Memory
    
    async def process():
        db = SessionLocal()
        try:
            # Получаем полную информацию о воспоминании
            memory = db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                return {"status": "error", "message": "Memory not found"}
            
            # Получение embedding
            try:
                embedding = await get_embedding(text)
            except Exception as e:
                return {"status": "error", "message": f"Failed to create embedding: {str(e)}"}
            
            # Сохранение в векторную БД (Qdrant или Pinecone)
            try:
                vector_id = await upsert_memory_embedding(
                    memory_id=memory_id,
                    memorial_id=memorial_id,
                    text=text,
                    embedding=embedding,
                    title=memory.title
                )
            except Exception as e:
                return {"status": "error", "message": f"Failed to save to vector DB: {str(e)}"}
            
            # Обновление записи в БД
            memory.embedding_id = vector_id
            db.commit()
            
            return {"status": "completed", "vector_id": vector_id}
        
        except Exception as e:
            # Повтор при ошибке
            raise self.retry(exc=e, countdown=60)
        
        finally:
            db.close()
    
    return asyncio.run(process())


# Для запуска worker'а:
# celery -A app.workers.worker worker --loglevel=info

