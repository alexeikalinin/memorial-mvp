#!/usr/bin/env python3
"""
Проверка EN-демо графа после seed_english_all.py (канон: en_memorials_manifest).

Запуск из backend/:
  source .venv/bin/activate && python verify_en_demo_graph.py

Выход ≠ 0 при ошибках. После смены сидов обновите критические проверки ниже.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

_sqlite = os.environ.get("SEED_USE_SQLITE", "").lower()
if _sqlite in ("1", "true", "yes"):
    os.environ["DATABASE_URL"] = os.environ.get("SEED_SQLITE_URL", "sqlite:///./memorial.db")

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import FamilyRelationship, Memorial, RelationshipType
from en_memorials_manifest import EXPECTED_EN_COUNT, EXPECTED_EN_NAMES

# Дублируется в tests/test_en_demo_canonical.py для регрессии без БД
CANONICAL_PARENT_CHECKS: list[tuple[str, frozenset[str]]] = [
    ("Emily Chang", frozenset({"David Chang", "Jennifer Park Chang"})),
    ("Serena Chang", frozenset({"David Chang", "Jennifer Park Chang"})),
    ("Daniel James Kelly", frozenset({"Michael Robert Kelly", "Catherine Kelly (O'Neill)"})),
    ("Sarah Elizabeth Kelly", frozenset({"Michael Robert Kelly", "Catherine Kelly (O'Neill)"})),
    ("Thomas Chang", frozenset({"Wei Chang", "Mei Lin Wu Chang"})),
    ("Wei Chang", frozenset({"Ah Fong Chang"})),
    ("Richard Chang", frozenset({"Thomas Chang", "Alice Lee Chang"})),
    ("David Chang", frozenset({"Richard Chang", "Grace Kim Chang"})),
    ("Antonio Rossi", frozenset({"Enzo Rossi", "Maria Conti Rossi"})),
    ("Marco Rossi", frozenset({"Antonio Rossi", "Giulia Moretti Rossi"})),
    ("Luca Rossi", frozenset({"Antonio Rossi", "Giulia Moretti Rossi"})),
]

CANONICAL_SPOUSE_PAIRS: list[tuple[str, str]] = [
    ("Michael Robert Kelly", "Catherine Kelly (O'Neill)"),
    ("James William Kelly", "Helen Margaret Anderson Kelly"),
    ("Emily Chang", "Daniel James Kelly"),
    ("Serena Chang", "Luca Rossi"),
    ("Wei Chang", "Mei Lin Wu Chang"),
]


def _name_by_id(db: Session, mid: int) -> str:
    m = db.query(Memorial).filter(Memorial.id == mid).first()
    return m.name if m else f"?id={mid}"


def parent_names_of(db: Session, child_name: str) -> set[str]:
    """Имена родителей по рёбрам PARENT (memorial=ребёнок, related=родитель)."""
    ch = db.query(Memorial).filter(Memorial.name == child_name).first()
    if not ch:
        return set()
    rels = (
        db.query(FamilyRelationship)
        .filter(
            FamilyRelationship.memorial_id == ch.id,
            FamilyRelationship.relationship_type == RelationshipType.PARENT,
        )
        .all()
    )
    out: set[str] = set()
    for r in rels:
        out.add(_name_by_id(db, r.related_memorial_id))
    return out


def has_spouse(db: Session, a: str, b: str) -> bool:
    ma = db.query(Memorial).filter(Memorial.name == a).first()
    mb = db.query(Memorial).filter(Memorial.name == b).first()
    if not ma or not mb:
        return False
    q1 = (
        db.query(FamilyRelationship)
        .filter(
            FamilyRelationship.memorial_id == ma.id,
            FamilyRelationship.related_memorial_id == mb.id,
            FamilyRelationship.relationship_type == RelationshipType.SPOUSE,
        )
        .first()
    )
    q2 = (
        db.query(FamilyRelationship)
        .filter(
            FamilyRelationship.memorial_id == mb.id,
            FamilyRelationship.related_memorial_id == ma.id,
            FamilyRelationship.relationship_type == RelationshipType.SPOUSE,
        )
        .first()
    )
    return q1 is not None or q2 is not None


def main() -> int:
    db = SessionLocal()
    errors: list[str] = []
    try:
        en = db.query(Memorial).filter(Memorial.language == "en").all()
        names = {m.name for m in en}
        if len(names) != EXPECTED_EN_COUNT:
            errors.append(f"EN memorial count {len(names)} != {EXPECTED_EN_COUNT}")
        missing = EXPECTED_EN_NAMES - names
        if missing:
            errors.append(f"missing EN names: {sorted(missing)}")
        extra = names - EXPECTED_EN_NAMES
        if extra:
            errors.append(f"extra EN names (not in manifest): {sorted(extra)}")

        for child, expected in CANONICAL_PARENT_CHECKS:
            got = parent_names_of(db, child)
            if got != expected:
                errors.append(f"parents of {child!r}: got {sorted(got)} expected {sorted(expected)}")

        for a, b in CANONICAL_SPOUSE_PAIRS:
            if not has_spouse(db, a, b):
                errors.append(f"missing spouse link: {a!r} ↔ {b!r}")

    finally:
        db.close()

    if errors:
        print("verify_en_demo_graph: FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("verify_en_demo_graph: OK (EN count, manifest names, parent/spouse checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
