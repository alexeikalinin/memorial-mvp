"""
Выдать пользователю роль OWNER для всех мемориалов (таблица memorial_access).

Использование из каталога backend/:
  source .venv/bin/activate
  python grant_owner_all_memorials.py you@example.com

Идемпотентно: существующую запись обновляет до OWNER; новые мемориалы после запуска
покрываются переменной окружения GLOBAL_ADMIN_EMAILS или повторным запуском скрипта.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import Base, Memorial, MemorialAccess, User, UserRole

Base.metadata.create_all(bind=engine)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python grant_owner_all_memorials.py <email>")
        sys.exit(1)
    email = sys.argv[1].strip().lower()
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email.ilike(email)).first()
        if not user:
            print(f"No user with email matching {email!r}")
            sys.exit(1)
        memorials = db.query(Memorial).all()
        n_new = 0
        n_upd = 0
        for m in memorials:
            row = (
                db.query(MemorialAccess)
                .filter(
                    MemorialAccess.memorial_id == m.id,
                    MemorialAccess.user_id == user.id,
                )
                .first()
            )
            if row is None:
                db.add(
                    MemorialAccess(
                        memorial_id=m.id,
                        user_id=user.id,
                        role=UserRole.OWNER,
                        granted_by=user.id,
                    )
                )
                n_new += 1
            elif row.role != UserRole.OWNER:
                row.role = UserRole.OWNER
                n_upd += 1
        db.commit()
        print(
            f"User id={user.id} ({user.email}): "
            f"{n_new} new OWNER rows, {n_upd} upgraded to OWNER, "
            f"{len(memorials)} memorials total."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
