"""
Скачивает портреты для англоязычных демо-мемориалов (Kelly / Anderson) и выставляет cover_photo_id.

Использует randomuser.me (nat=au,gb,ie,nz — «англоязычный» внешний контекст для инвесторов).
Подбирает возраст на фото грубо под поколение персонажа.

Запуск из backend/:
    source .venv/bin/activate && python seed_english_portraits.py

Требует: сеть. Идемпотентно пропускает мемориалы, у которых уже есть cover_photo_id.
"""

from __future__ import annotations

import io
import os
import sys
import time
import uuid
from pathlib import Path

import requests
from PIL import Image
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.db import engine
from app.models import Media, Memorial, MediaType
from app.services.media_service import generate_all_thumbnails

UPLOADS = Path("uploads")
THUMBNAILS_DIR = UPLOADS / "thumbnails"
UPLOADS.mkdir(exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

# Англоязычные страны randomuser (внешность и контекст ближе к AU/NZ/UK демо)
NATS = "au,gb,ie,nz"

# memorial_id → подбор «возраста на фото» и пол (соответствует voice_gender / персонажу)
TARGETS: list[dict] = [
    {"memorial_id": 22, "gender": "male", "age_min": 62, "age_max": 78},  # Sean
    {"memorial_id": 23, "gender": "female", "age_min": 65, "age_max": 82},  # Brigid
    {"memorial_id": 24, "gender": "male", "age_min": 68, "age_max": 85},  # Thomas
    {"memorial_id": 25, "gender": "female", "age_min": 68, "age_max": 85},  # Rose
    {"memorial_id": 26, "gender": "male", "age_min": 55, "age_max": 72},  # James
    {"memorial_id": 27, "gender": "male", "age_min": 62, "age_max": 80},  # Duncan
    {"memorial_id": 28, "gender": "female", "age_min": 65, "age_max": 82},  # Flora
    {"memorial_id": 29, "gender": "male", "age_min": 58, "age_max": 75},  # William
    {"memorial_id": 30, "gender": "female", "age_min": 62, "age_max": 80},  # Agnes
    {"memorial_id": 31, "gender": "female", "age_min": 62, "age_max": 80},  # Helen
    {"memorial_id": 32, "gender": "male", "age_min": 52, "age_max": 70},  # Robert
    # New memorials (added 2026-03-28)
    {"memorial_id": 33, "gender": "female", "age_min": 55, "age_max": 75},  # Patricia
    {"memorial_id": 34, "gender": "male", "age_min": 45, "age_max": 62},   # Michael
    {"memorial_id": 35, "gender": "female", "age_min": 45, "age_max": 65}, # Catherine (alive)
    {"memorial_id": 36, "gender": "female", "age_min": 25, "age_max": 40}, # Sarah (alive)
    {"memorial_id": 37, "gender": "male", "age_min": 25, "age_max": 38},   # Daniel (alive)
    {"memorial_id": 38, "gender": "male", "age_min": 55, "age_max": 72},   # George
    {"memorial_id": 39, "gender": "female", "age_min": 60, "age_max": 80}, # Margaret
    {"memorial_id": 40, "gender": "male", "age_min": 75, "age_max": 95},   # Ian (alive, 93)
    {"memorial_id": 41, "gender": "female", "age_min": 70, "age_max": 90}, # Evelyn (alive, 90)
    # Chang family (Chinese-Australian) — nat=cn,au for East-Asian appearance
    {"memorial_id": 42, "gender": "male",   "age_min": 55, "age_max": 75,  "nat": "cn"},  # Ah Fong (portrait age ≠ birth year)
    {"memorial_id": 43, "gender": "male",   "age_min": 55, "age_max": 75,  "nat": "cn"},  # Wei
    {"memorial_id": 44, "gender": "female", "age_min": 55, "age_max": 75,  "nat": "cn"},  # Mei Lin
    {"memorial_id": 45, "gender": "male",   "age_min": 55, "age_max": 75,  "nat": "cn"},  # Thomas
    {"memorial_id": 46, "gender": "female", "age_min": 55, "age_max": 75,  "nat": "cn"},  # Alice
    {"memorial_id": 47, "gender": "male",   "age_min": 55, "age_max": 75,  "nat": "cn"},  # Richard
    {"memorial_id": 48, "gender": "female", "age_min": 55, "age_max": 75,  "nat": "cn"},  # Grace (alive)
    {"memorial_id": 49, "gender": "male",   "age_min": 30, "age_max": 50,  "nat": "cn"},  # David (alive)
    {"memorial_id": 50, "gender": "female", "age_min": 30, "age_max": 50,  "nat": "cn"},  # Jennifer (alive)
    # Rossi family (Italian-Australian) — nat=it,au
    {"memorial_id": 51, "gender": "male",   "age_min": 55, "age_max": 75,  "nat": "it"},  # Enzo
    {"memorial_id": 52, "gender": "female", "age_min": 55, "age_max": 75,  "nat": "it"},  # Maria
    {"memorial_id": 53, "gender": "male",   "age_min": 45, "age_max": 65,  "nat": "it"},  # Antonio (alive)
    {"memorial_id": 54, "gender": "female", "age_min": 45, "age_max": 65,  "nat": "it"},  # Giulia (alive)
    {"memorial_id": 55, "gender": "male",   "age_min": 25, "age_max": 45,  "nat": "it"},  # Marco (alive)
    {"memorial_id": 56, "gender": "female", "age_min": 25, "age_max": 45,  "nat": "it"},  # Sofia (alive)
]


def fetch_portrait(gender: str, age_min: int, age_max: int, attempts: int = 40, nat: str | None = None) -> bytes | None:
    use_nat = nat if nat else NATS
    url = f"https://randomuser.me/api/?gender={gender}&nat={use_nat}&results=1"
    session = requests.Session()
    for i in range(attempts):
        try:
            r = session.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            user = data["results"][0]
            age = user["dob"]["age"]
            if age_min <= age <= age_max:
                photo_url = user["picture"]["large"]
                r2 = session.get(photo_url, timeout=15)
                r2.raise_for_status()
                print(f"    ✓ age={age} (try {i + 1})")
                return r2.content
            print(f"    ~ age={age} not in [{age_min}-{age_max}], skip...")
        except Exception as e:
            print(f"    ! {e}, retry...")
        time.sleep(1.2)
    return None


def save_and_optimize(photo_bytes: bytes, memorial_id: int) -> tuple[Path, str, int]:
    img = Image.open(io.BytesIO(photo_bytes))
    img = img.convert("RGB")
    img = img.resize((600, 600), Image.LANCZOS)
    uid = uuid.uuid4()
    fname = f"{uid}_en_portrait_m{memorial_id}.jpg"
    fpath = UPLOADS / fname
    img.save(str(fpath), "JPEG", quality=88, optimize=True)
    size = fpath.stat().st_size
    return fpath, fname, size


def run():
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    ok = 0
    skip = 0
    fail = 0
    try:
        for t in TARGETS:
            mid = t["memorial_id"]
            memorial = db.query(Memorial).filter(Memorial.id == mid).first()
            if not memorial:
                print(f"[{mid}] memorial missing, skip")
                fail += 1
                continue
            if memorial.language != "en":
                print(f"[{mid}] not EN, skip")
                fail += 1
                continue
            if memorial.cover_photo_id:
                print(f"\n[{mid}] {memorial.name} — already has cover_photo_id={memorial.cover_photo_id}, skip")
                skip += 1
                continue

            print(f"\n[{mid}] {memorial.name} → {t['gender']}, photo age {t['age_min']}-{t['age_max']}")
            photo_bytes = fetch_portrait(t["gender"], t["age_min"], t["age_max"], nat=t.get("nat"))
            if not photo_bytes:
                print("  ✗ could not fetch portrait")
                fail += 1
                continue

            file_path, fname, fsize = save_and_optimize(photo_bytes, mid)

            thumbnails = generate_all_thumbnails(file_path, THUMBNAILS_DIR)
            thumb_medium = thumbnails.get("medium")

            media = Media(
                memorial_id=mid,
                file_path=str(file_path),
                file_name=fname,
                file_size=fsize,
                mime_type="image/jpeg",
                media_type=MediaType.PHOTO,
                thumbnail_path=thumb_medium,
            )
            db.add(media)
            db.flush()
            memorial.cover_photo_id = media.id
            db.commit()
            print(f"  ✓ media.id={media.id}, cover set, thumb={thumb_medium}")
            ok += 1

        print(f"\n═══ Done: {ok} portraits, {skip} skipped (had cover), {fail} failed ═══")
    finally:
        db.close()


if __name__ == "__main__":
    run()
