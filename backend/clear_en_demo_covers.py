"""
Сбрасывает cover_photo_id у всех EN-демо из `portrait_params_en` (канонические имена),
чтобы заново подтянуть портреты после исправления seed_english_portraits (привязка по имени).

  cd backend && source .venv/bin/activate && SEED_USE_SQLITE=1 python clear_en_demo_covers.py && SEED_USE_SQLITE=1 python seed_english_portraits.py

Без `SEED_USE_SQLITE=1` используется `DATABASE_URL` из `.env` (часто удалённый Supabase) — локальный `memorial.db` после rebuild не затронется.

Требуется сеть для seed_english_portraits.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

_sqlite = os.environ.get("SEED_USE_SQLITE", "").lower() in ("1", "true", "yes")
if _sqlite:
    os.environ["DATABASE_URL"] = os.environ.get("SEED_SQLITE_URL", "sqlite:///./memorial.db")

from sqlalchemy.orm import sessionmaker

from app.db import engine
from app.models import Memorial
from portrait_params_en import PORTRAIT_PARAMS_BY_NAME


def main():
    Session = sessionmaker(bind=engine)
    db = Session()
    n = 0
    try:
        for name in PORTRAIT_PARAMS_BY_NAME:
            m = (
                db.query(Memorial)
                .filter(Memorial.name == name, Memorial.language == "en")
                .first()
            )
            if m and m.cover_photo_id is not None:
                m.cover_photo_id = None
                n += 1
        db.commit()
        print(f"Cleared cover_photo_id on {n} EN demo memorial(s). Run: python seed_english_portraits.py")
    finally:
        db.close()


if __name__ == "__main__":
    main()
