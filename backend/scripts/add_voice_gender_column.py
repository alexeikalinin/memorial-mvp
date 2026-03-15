#!/usr/bin/env python3
"""
Добавить колонку voice_gender в таблицу memorials (если её ещё нет).
Для PostgreSQL (Supabase): ALTER TABLE memorials ADD COLUMN IF NOT EXISTS voice_gender VARCHAR(20);
Запуск из корня backend: python -m scripts.add_voice_gender_column
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db import engine
from app.config import settings


def main():
    url = settings.DATABASE_URL
    if "sqlite" in url:
        # SQLite: ADD COLUMN не поддерживает IF NOT EXISTS в старых версиях
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE memorials ADD COLUMN voice_gender VARCHAR(20)"))
                conn.commit()
                print("✅ Колонка voice_gender добавлена в SQLite.")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("ℹ️ Колонка voice_gender уже есть в SQLite.")
                else:
                    raise
        return
    if "postgresql" in url or "postgres" in url:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE memorials ADD COLUMN IF NOT EXISTS voice_gender VARCHAR(20)"))
            conn.commit()
        print("✅ Колонка voice_gender добавлена в PostgreSQL (или уже была).")
        return
    print("Неизвестный тип БД. Добавьте колонку вручную: ALTER TABLE memorials ADD COLUMN voice_gender VARCHAR(20);")


if __name__ == "__main__":
    main()
