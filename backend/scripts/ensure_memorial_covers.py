"""
Ставит cover_photo_id там, где он пустой, но в мемориале уже есть фото (первое по id).

Если обложки нет и фото нет — только печатает id в списке «нужен портрет» (как fix_memorial_photos / seed).

Запуск (из каталога backend):
  source .venv/bin/activate
  python scripts/ensure_memorial_covers.py
  python scripts/ensure_memorial_covers.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Media, Memorial, MediaType


def run(db: Session, dry_run: bool) -> None:
    missing_cover = (
        db.query(Memorial)
        .filter(Memorial.cover_photo_id.is_(None))
        .order_by(Memorial.id)
        .all()
    )
    fixed = []
    still_empty = []
    for m in missing_cover:
        first_photo = (
            db.query(Media)
            .filter(
                Media.memorial_id == m.id,
                Media.media_type == MediaType.PHOTO,
            )
            .order_by(Media.id)
            .first()
        )
        if first_photo:
            if not dry_run:
                m.cover_photo_id = first_photo.id
            fixed.append((m.id, m.name, first_photo.id))
        else:
            still_empty.append((m.id, m.name))

    if not dry_run and fixed:
        db.commit()

    print(f"Memorials without cover before: {len(missing_cover)}")
    print(f"Assigned first photo as cover: {len(fixed)}")
    for mid, name, pid in fixed:
        print(f"  ✓ id={mid} {name!r} → media_id={pid}")
    if still_empty:
        print(f"Still no photo in DB (need upload or fix_memorial_photos): {len(still_empty)}")
        for mid, name in still_empty:
            print(f"  · id={mid} {name!r}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    db = SessionLocal()
    try:
        run(db, args.dry_run)
    finally:
        db.close()


if __name__ == "__main__":
    main()
