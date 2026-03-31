"""
Проставить is_public всем мемориалам (для демо: публичные страницы /m/:id).

  cd backend && source .venv/bin/activate && python set_all_memorials_public.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.db import SessionLocal, engine
from app.models import Base, Memorial

Base.metadata.create_all(bind=engine)


def main() -> None:
    db = SessionLocal()
    try:
        rows = db.query(Memorial).all()
        n = 0
        for m in rows:
            if not m.is_public:
                m.is_public = True
                n += 1
        db.commit()
        print(f"Set is_public=True for {n} memorial(s) (out of {len(rows)} total).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
