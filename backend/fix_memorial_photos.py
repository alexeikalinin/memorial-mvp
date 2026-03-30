"""
Скачивает подходящие портреты с randomuser.me и обновляет cover_photo_id
для всех мемориалов без фото + исправляет несоответствие по возрасту.

Запуск:
  cd backend
  source .venv/bin/activate
  python fix_memorial_photos.py
"""

import os, sys, uuid, time, json
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

# ── Описание желаемых фото для каждого memorial_id ────────────────
# gender: male/female   age_min/age_max: диапазон возраста на фото
TARGETS = [
    # ── Оставшиеся без фото (повторный запуск) ──────────────────
    dict(memorial_id=32, gender="male",   age_min=60, age_max=80),  # Пётр (1896-1968)
    dict(memorial_id=33, gender="male",   age_min=55, age_max=70),  # Сергей (1926-2001)
    dict(memorial_id=34, gender="female", age_min=70, age_max=85),  # Людмила (1929)
    dict(memorial_id=35, gender="female", age_min=55, age_max=68),  # Алёна (1956)
    dict(memorial_id=36, gender="female", age_min=50, age_max=65),  # Ирина (1959)
    dict(memorial_id=37, gender="male",   age_min=35, age_max=48),  # Виктор (1979)
    dict(memorial_id=38, gender="female", age_min=30, age_max=45),  # Полина (1982)
    dict(memorial_id=39, gender="male",   age_min=65, age_max=80),  # Евгений (1870-1944)
    dict(memorial_id=40, gender="male",   age_min=55, age_max=70),  # Борис (1905-1978)
    dict(memorial_id=41, gender="female", age_min=70, age_max=85),  # Наталья (1932)
    dict(memorial_id=42, gender="male",   age_min=50, age_max=65),  # Дмитрий (1960)
]

# Национальности с европейской/славянской внешностью в randomuser.me
NATS = "gb,ie,au,nz,fi,no,dk,nl"


def fetch_portrait(gender: str, age_min: int, age_max: int, attempts: int = 30) -> bytes | None:
    """Скачивает фото подходящего возраста из randomuser.me."""
    url = f"https://randomuser.me/api/?gender={gender}&nat={NATS}&results=1"
    session = requests.Session()
    for i in range(attempts):
        try:
            r = session.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            user = data["results"][0]
            age = user["dob"]["age"]
            if age_min <= age <= age_max:
                photo_url = user["picture"]["large"]
                r2 = session.get(photo_url, timeout=10)
                r2.raise_for_status()
                print(f"    ✓ возраст={age} (попытка {i+1})")
                return r2.content
            else:
                print(f"    ~ возраст={age} не подходит [{age_min}-{age_max}], пропуск...")
        except Exception as e:
            print(f"    ! ошибка {e}, повтор...")
        time.sleep(1.5)
    return None


def save_and_optimize(photo_bytes: bytes, memorial_id: int) -> tuple[str, str, int]:
    """Оптимизирует изображение, сохраняет, возвращает (file_path, file_name, size)."""
    img = Image.open(io.BytesIO(photo_bytes))

    # Конвертируем в RGB и увеличиваем до 600x600 через Lanczos
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

            print(f"\n[{mid}] {memorial.name} → {t['gender']}, {t['age_min']}-{t['age_max']} лет")

            photo_bytes = fetch_portrait(t["gender"], t["age_min"], t["age_max"])
            if not photo_bytes:
                print(f"  ✗ не удалось скачать фото")
                fail += 1
                continue

            fpath, fname, fsize = save_and_optimize(photo_bytes, mid)

            # Удаляем старое cover_photo если меняем (только для 20/21)
            if memorial.cover_photo_id and mid in (20, 21):
                old_media = db.query(Media).filter(Media.id == memorial.cover_photo_id).first()
                if old_media:
                    try:
                        old_file = Path(old_media.file_path)
                        if old_file.exists():
                            old_file.unlink()
                    except Exception:
                        pass

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

        print(f"\n═══ Готово: {ok} обновлено, {fail} не удалось ═══")
    finally:
        db.close()


if __name__ == "__main__":
    run()
