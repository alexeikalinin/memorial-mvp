"""
Идемпотентно добавить CUSTOM-мосты Kelly/Anderson ↔ Chang/Rossi в family_relationships,
чтобы GET .../full-tree с любого демо-мемориала видел все 4 кластера (одна компонента).

  cd backend && source .venv/bin/activate && python link_cross_cluster_bridges.py

Те же пары, что в seed_english_cluster2.CROSS_CLUSTER_CUSTOM_BRIDGES.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.db import SessionLocal
from app.models import FamilyRelationship, Memorial, RelationshipType

BRIDGES = [
    ("Sean Patrick Kelly", "Ah Fong Chang"),
    ("Wei Chang", "Agnes Brown Anderson"),
    ("Robert James Kelly", "Enzo Rossi"),
    ("Michael Robert Kelly", "Antonio Rossi"),
    ("Antonio Rossi", "Ian George Anderson"),
]


def main() -> None:
    db = SessionLocal()
    try:
        added = 0
        for name_a, name_b in BRIDGES:
            ma = db.query(Memorial).filter(Memorial.name == name_a).first()
            mb = db.query(Memorial).filter(Memorial.name == name_b).first()
            if not ma or not mb:
                print(f"Skip (missing): {name_a!r} ↔ {name_b!r}")
                continue
            rt = RelationshipType.CUSTOM
            for src, dst in ((ma.id, mb.id), (mb.id, ma.id)):
                exists = (
                    db.query(FamilyRelationship)
                    .filter(
                        FamilyRelationship.memorial_id == src,
                        FamilyRelationship.related_memorial_id == dst,
                        FamilyRelationship.relationship_type == rt,
                    )
                    .first()
                )
                if exists:
                    continue
                db.add(
                    FamilyRelationship(
                        memorial_id=src,
                        related_memorial_id=dst,
                        relationship_type=rt,
                    )
                )
                added += 1
                print(f"Added CUSTOM {src} → {dst}")
        db.commit()
        print(f"Done. New relationship rows: {added}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
