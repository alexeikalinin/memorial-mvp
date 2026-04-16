"""
Скачивает портреты для англоязычных демо-мемориалов (Kelly / Anderson) и выставляет cover_photo_id.

Использует randomuser.me (nat=au,gb,ie,nz — «англоязычный» внешний контекст для инвесторов).
Подбирает возраст на фото грубо под поколение персонажа.

Запуск из backend/:
    source .venv/bin/activate && python seed_english_portraits.py

Локальный SQLite (если в `.env` указан Supabase, а нужен только `memorial.db`):
    SEED_USE_SQLITE=1 python seed_english_portraits.py

Требует: сеть. Идемпотентно пропускает мемориалы, у которых уже есть cover_photo_id.

Портреты привязываются к **точному имени** (`portrait_params_en.PORTRAIT_PARAMS_BY_NAME`), не к `memorial_id`,
чтобы не путать обложки при любом порядке вставки сидов.

Если в БД уже стоят **неправильные** обложки (старый запуск по id): сбросьте `cover_photo_id` для нужных EN-мемориалов
или для всех `language='en'`, затем снова `python seed_english_portraits.py`.
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

_sqlite_flag = os.environ.get("SEED_USE_SQLITE", "").lower()
if _sqlite_flag in ("1", "true", "yes"):
    os.environ["DATABASE_URL"] = os.environ.get("SEED_SQLITE_URL", "sqlite:///./memorial.db")

from app.db import engine
from app.models import Media, Memorial, MediaType
from app.services.media_service import generate_all_thumbnails
from portrait_params_en import PORTRAIT_PARAMS_BY_NAME

UPLOADS = Path("uploads")
THUMBNAILS_DIR = UPLOADS / "thumbnails"
UPLOADS.mkdir(exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

# Англоязычные страны randomuser (внешность и контекст ближе к AU/NZ/UK демо)
NATS = "au,gb,ie,nz"


def _explicit_fallback_by_name() -> dict[str, dict]:
    return PORTRAIT_PARAMS_BY_NAME


def _params_for_en_memorial(memorial: Memorial) -> dict:
    """Пол/возраст/nat для randomuser, если нет записи в PORTRAIT_PARAMS_BY_NAME."""
    fb = _explicit_fallback_by_name()
    if memorial.name in fb:
        return fb[memorial.name]
    vg = (memorial.voice_gender or "male").lower()
    gender = "male" if vg == "male" else "female"
    n = memorial.name
    if "Chang" in n:
        return {"gender": gender, "age_min": 22, "age_max": 78, "nat": "cn"}
    if "Rossi" in n:
        return {"gender": gender, "age_min": 25, "age_max": 82, "nat": "it"}
    return {"gender": gender, "age_min": 28, "age_max": 92, "nat": None}


def _set_cover_from_params(db, memorial: Memorial, p: dict) -> bool:
    mid = memorial.id
    photo_bytes = fetch_portrait(
        p["gender"], p["age_min"], p["age_max"], nat=p.get("nat")
    )
    if not photo_bytes:
        print("  ✗ could not fetch portrait")
        return False
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
    return True


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
        for name in sorted(PORTRAIT_PARAMS_BY_NAME.keys()):
            t = PORTRAIT_PARAMS_BY_NAME[name]
            memorial = (
                db.query(Memorial)
                .filter(Memorial.name == name, Memorial.language == "en")
                .first()
            )
            if not memorial:
                fail += 1
                continue
            if memorial.cover_photo_id:
                print(f"\n[{memorial.id}] {memorial.name} — already has cover_photo_id={memorial.cover_photo_id}, skip")
                skip += 1
                continue

            mid = memorial.id
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

        print("\n── Remaining EN memorials without cover (имена вне канонического списка) ──")
        remaining = (
            db.query(Memorial)
            .filter(Memorial.language == "en", Memorial.cover_photo_id.is_(None))
            .order_by(Memorial.id)
            .all()
        )
        for memorial in remaining:
            p = _params_for_en_memorial(memorial)
            print(
                f"\n[fill] [{memorial.id}] {memorial.name} → {p['gender']}, "
                f"photo age {p['age_min']}-{p['age_max']}, nat={p.get('nat') or NATS}"
            )
            if _set_cover_from_params(db, memorial, p):
                ok += 1
            else:
                fail += 1

        print(f"\n═══ Done: {ok} portraits, {skip} skipped (had cover), {fail} failed ═══")
    finally:
        db.close()


if __name__ == "__main__":
    run()
