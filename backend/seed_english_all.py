"""
Полная английская демо-наполнение БД: ровно 35 мемориалов (language='en').

Запуск из каталога backend/:
    source .venv/bin/activate && python seed_english_all.py

Порядок (зависимости между сидами):
  1. seed_english.py            — 11 (Kelly + Anderson, поколения до Robert)
  2. seed_english_expanded.py   — +9 → 20
  3. seed_english_cluster2.py  — +15 (Chang + Rossi) → 35

Опционально портреты (локально / при настроенном S3):
    python seed_english_portraits.py
    # или для прод-стораджа: python seed_prod_portraits.py

Проверка числа: en_memorials_manifest.EXPECTED_EN_COUNT
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import text  # noqa: E402

from app.db import engine  # noqa: E402
from en_memorials_manifest import EXPECTED_EN_COUNT, EXPECTED_EN_NAMES  # noqa: E402


async def main() -> None:
    from seed_english import seed as seed_base
    from seed_english_expanded import seed as seed_expanded
    from seed_english_cluster2 import seed as seed_cluster2

    print("=== (1/3) seed_english.py …")
    await seed_base()
    print("\n=== (2/3) seed_english_expanded.py …")
    await seed_expanded()
    print("\n=== (3/3) seed_english_cluster2.py …")
    await seed_cluster2()

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM memorials WHERE language = 'en'")).scalar_one()
        rows = conn.execute(
            text("SELECT name FROM memorials WHERE language = 'en'")
        ).fetchall()
    names = {r[0] for r in rows}

    print(f"\n✅ EN memorials in DB: {n} (expected {EXPECTED_EN_COUNT})")
    missing = EXPECTED_EN_NAMES - names
    extra = names - EXPECTED_EN_NAMES
    if missing:
        print(f"❌ Missing names vs manifest ({len(missing)}):", sorted(missing))
    if extra:
        print(f"⚠️ Extra names not in manifest ({len(extra)}):", sorted(extra))
    if n != EXPECTED_EN_COUNT or missing or extra:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
