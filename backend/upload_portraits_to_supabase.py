"""
Загружает локальные портреты (media.id 11-33) в Supabase Storage.
Нужно запустить один раз чтобы исправить отображение фото.

Запуск:
  cd backend
  source .venv/bin/activate
  python upload_portraits_to_supabase.py
"""

import os, sys
from pathlib import Path

sys.path.insert(0, '.')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.db import engine
from app.models import Media
from app.services.s3_service import upload_file_to_s3

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Все наши новые портреты (media.id 11-33)
    medias = db.query(Media).filter(Media.id >= 11, Media.id <= 33).all()
    print(f"Найдено {len(medias)} медиа-записей\n")

    ok = 0
    fail = 0
    for m in medias:
        local_path = Path(m.file_path)
        if not local_path.exists():
            print(f"  [id={m.id}] ✗ файл не найден локально: {m.file_path}")
            fail += 1
            continue

        # S3 key = file_path (например uploads/xxx.jpg)
        s3_key = m.file_path
        result = upload_file_to_s3(local_path, s3_key, content_type="image/jpeg")
        if result:
            print(f"  [id={m.id}] ✓ загружен: {m.file_name}")
            ok += 1
        else:
            print(f"  [id={m.id}] ✗ ошибка загрузки: {m.file_name}")
            fail += 1

    print(f"\n═══ Готово: {ok} загружено, {fail} не удалось ═══")
finally:
    db.close()
