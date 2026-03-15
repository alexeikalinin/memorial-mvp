#!/usr/bin/env python3
"""
Проверка дубликатов мемориалов в БД (по owner_id + name).
Запуск из корня backend: python -m scripts.check_duplicate_memorials
"""
import sys
from pathlib import Path

# Добавляем backend в path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func
from app.db import SessionLocal
from app.models import Memorial


def main():
    db = SessionLocal()
    try:
        total = db.query(Memorial).count()
        print(f"Всего мемориалов в БД: {total}")

        memorials = db.query(Memorial).order_by(Memorial.created_at.desc()).all()
        for m in memorials:
            print(f"  id={m.id} owner_id={m.owner_id} name={repr(m.name)} created_at={m.created_at}")

        # Дубликаты: одинаковые (owner_id, name)
        dups = (
            db.query(Memorial.owner_id, Memorial.name, func.count(Memorial.id).label("cnt"))
            .group_by(Memorial.owner_id, Memorial.name)
            .having(func.count(Memorial.id) > 1)
            .all()
        )
        if dups:
            print(f"\nНайдены дубликаты (owner_id, name) — {len(dups)} групп:")
            for owner_id, name, cnt in dups:
                rows = db.query(Memorial).filter(Memorial.owner_id == owner_id, Memorial.name == name).order_by(Memorial.id).all()
                print(f"  owner_id={owner_id} name={repr(name)} count={cnt} ids={[r.id for r in rows]}")
        else:
            print("\nДубликатов по (owner_id, name) не найдено.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
