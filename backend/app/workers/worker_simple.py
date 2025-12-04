"""
Простой worker без Celery (для новичков).
Использует polling базы данных для поиска задач.
"""
import time
import asyncio
from app.db import SessionLocal
from app.models import Media, MediaType
from app.services.ai_tasks import animate_photo_did, get_did_talk_status


async def process_animation_tasks():
    """
    Обработка задач анимации фото.
    Ищет медиа с animation_task_id=None и media_type=PHOTO.
    """
    db = SessionLocal()
    try:
        # Поиск фото, которые нужно анимировать
        # В реальности лучше использовать отдельную таблицу tasks
        pending_media = db.query(Media).filter(
            Media.media_type == MediaType.PHOTO,
            Media.is_animated == False,
            Media.animation_task_id == None
        ).limit(5).all()
        
        for media in pending_media:
            try:
                # TODO: Получить публичный URL изображения
                image_url = f"http://localhost:8000/{media.file_path}"
                
                # Запуск анимации
                result = await animate_photo_did(image_url)
                talk_id = result.get("id")
                
                # Сохранение task_id
                media.animation_task_id = talk_id
                db.commit()
                
                print(f"Started animation for media {media.id}, talk_id: {talk_id}")
            
            except Exception as e:
                print(f"Error processing media {media.id}: {e}")
        
        # Проверка статуса активных задач
        active_media = db.query(Media).filter(
            Media.animation_task_id != None,
            Media.is_animated == False
        ).all()
        
        for media in active_media:
            try:
                status_result = await get_did_talk_status(media.animation_task_id)
                status = status_result.get("status")
                
                if status == "done":
                    video_url = status_result.get("result_url")
                    media.file_url = video_url
                    media.is_animated = True
                    media.media_type = MediaType.VIDEO
                    db.commit()
                    print(f"Animation completed for media {media.id}")
                elif status == "error":
                    print(f"Animation failed for media {media.id}")
                    # Можно пометить как failed или повторить
        
            except Exception as e:
                print(f"Error checking status for media {media.id}: {e}")
    
    finally:
        db.close()


def run_worker():
    """
    Запуск простого worker'а в цикле.
    """
    print("Starting simple worker...")
    while True:
        try:
            asyncio.run(process_animation_tasks())
        except KeyboardInterrupt:
            print("Worker stopped")
            break
        except Exception as e:
            print(f"Worker error: {e}")
        
        time.sleep(10)  # Проверка каждые 10 секунд


if __name__ == "__main__":
    run_worker()

