"""
Fix Robert ↔ Patricia relationship from SPOUSE → EX_SPOUSE.
Run once: python fix_robert_patricia_ex_spouse.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.database_url)

ROBERT_NAME = "Robert James Kelly"
PATRICIA_NAME = "Patricia Ann Murphy Kelly"

with engine.connect() as conn:
    # Find memorial IDs
    robert_row = conn.execute(
        text("SELECT id FROM memorials WHERE name = :name LIMIT 1"),
        {"name": ROBERT_NAME}
    ).fetchone()
    patricia_row = conn.execute(
        text("SELECT id FROM memorials WHERE name = :name LIMIT 1"),
        {"name": PATRICIA_NAME}
    ).fetchone()

    if not robert_row or not patricia_row:
        print(f"Could not find memorials: Robert={robert_row}, Patricia={patricia_row}")
        sys.exit(1)

    robert_id = robert_row[0]
    patricia_id = patricia_row[0]
    print(f"Robert id={robert_id}, Patricia id={patricia_id}")

    # Update both directions
    result = conn.execute(
        text("""
            UPDATE family_relationships
            SET relationship_type = 'EX_SPOUSE'
            WHERE (memorial_id = :r AND related_memorial_id = :p)
               OR (memorial_id = :p AND related_memorial_id = :r)
        """),
        {"r": robert_id, "p": patricia_id}
    )
    print(f"Updated {result.rowcount} rows to EX_SPOUSE")
    conn.commit()

print("Done.")
