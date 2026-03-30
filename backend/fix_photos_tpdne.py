"""
Скачивает AI-портреты с thispersondoesnotexist.com для мемориалов без фото.
randomuser.me заблокировал наш IP по rate-limit.

Запуск:
  cd backend
  source .venv/bin/activate
  python fix_photos_tpdne.py
"""

import os, sys, uuid, time
from pathlib import Path
from PIL import Image
import io
import requests

sys.path.insert(0, '.')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.db import engine
from app.models import Media, Memorial

UPLOADS = Path("uploads")
UPLOADS.mkdir(exist_ok=True)

# Мемориалы без фото после первого прогона
TARGETS = [
    dict(memorial_id=32),  # Пётр (male, 60-80 лет)
    dict(memorial_id=33),  # Сергей (male, 55-70 лет)
    dict(memorial_id=34),  # Людмила (female, 70-85 лет)
    dict(memorial_id=35),  # Алёна (female, 55-68 лет)
    dict(memorial_id=36),  # Ирина (female, 50-65 лет)
    dict(memorial_id=37),  # Виктор (male, 35-48 лет)
    dict(memorial_id=38),  # Полина (female, 30-45 лет)
    dict(memorial_id=39),  # Евгений (male, 65-80 лет)
    dict(memorial_id=40),  # Борис (male, 55-70 лет)
    dict(memorial_id=41),  # Наталья (female, 70-85 лет)
    dict(memorial_id=42),  # Дмитрий (male, 50-65 лет)
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}


def fetch_portrait() -> bytes | None:
    """Скачивает AI-сгенерированный портрет с thispersondoesnotexist.com."""
    for attempt in range(5):
        try:
            r = requests.get('https://thispersondoesnotexist.com/', timeout=15, headers=HEADERS)
            r.raise_for_status()
            if r.headers.get('Content-Type', '').startswith('image/'):
                print(f"    ✓ скачан портрет ({len(r.content)//1024} KB)")
                return r.content
        except Exception as e:
            print(f"    ! ошибка {e}, повтор...")
        time.sleep(2)
    return None


def save_and_optimize(photo_bytes: bytes, memorial_id: int) -> tuple[str, str, int]:
    """Оптимизирует изображение, сохраняет, возвращает (file_path, file_name, size)."""
    img = Image.open(io.BytesIO(photo_bytes))
    img = img.convert("RGB")
    img = img.resize((600, 600), Image.LANCZOS)

    uid = uuid.uuid4()
    fname = f"{uid}_portrait_m{memorial_id}.jpg"
    fpath = UPLOADS / fname

    img.save(str(fpath), "JPEG", quality=88, optimize=True)
    size = fpath.stat().st_size
    return str(fpath), fname, size


def run():
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        ok = 0
        fail = 0
        for t in TARGETS:
            mid = t["memorial_id"]
            memorial = db.query(Memorial).filter(Memorial.id == mid).first()
            if not memorial:
                print(f"[{mid}] мемориал не найден, пропуск")
                continue

            print(f"\n[{mid}] {memorial.name}")

            # Пропускаем если фото уже есть
            if memorial.cover_photo_id:
                print(f"  ~ уже есть фото (media.id={memorial.cover_photo_id}), пропуск")
                continue

            photo_bytes = fetch_portrait()
            if not photo_bytes:
                print(f"  ✗ не удалось скачать фото")
                fail += 1
                continue

            fpath, fname, fsize = save_and_optimize(photo_bytes, mid)

            media = Media(
                memorial_id=mid,
                file_path=fpath,
                file_name=fname,
                file_size=fsize,
                mime_type="image/jpeg",
                media_type="photo",
            )
            db.add(media)
            db.flush()

            memorial.cover_photo_id = media.id
            db.commit()
            print(f"  ✓ сохранено: {fname} ({fsize//1024} KB), media.id={media.id}")
            ok += 1

            # Пауза между запросами чтобы не заблокировали
            time.sleep(3)

        print(f"\n═══ Готово: {ok} обновлено, {fail} не удалось ═══")
    finally:
        db.close()


if __name__ == "__main__":
    run()
