#!/usr/bin/env python3
"""
Проставить voice_gender (male/female) у мемориалов по имени.
Запуск: python -m scripts.set_voice_gender_by_name
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Memorial

# Первые имена, по которым определяем пол (русские)
FEMALE_FIRST_NAMES = {
    "анна", "мария", "прасковья", "людмила", "светлана", "елена", "ольга",
    "наталья", "татьяна", "ирина", "екатерина", "надежда", "валентина",
    "марья", "марина", "виктория", "юлия", "александра", "дарья", "полина",
}


def get_first_name(full_name: str) -> str:
    """Первое слово (имя) в нижнем регистре."""
    if not full_name or not full_name.strip():
        return ""
    return full_name.strip().split()[0].lower()


def main():
    db = SessionLocal()
    try:
        memorials = db.query(Memorial).all()
        updated = 0
        for m in memorials:
            first = get_first_name(m.name or "")
            if not first:
                continue
            if first in FEMALE_FIRST_NAMES:
                if m.voice_gender != "female":
                    m.voice_gender = "female"
                    updated += 1
                    print(f"  {m.name} → female")
            else:
                if m.voice_gender != "male":
                    m.voice_gender = "male"
                    updated += 1
                    print(f"  {m.name} → male")
        db.commit()
        print(f"\n✅ Обновлено мемориалов: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
