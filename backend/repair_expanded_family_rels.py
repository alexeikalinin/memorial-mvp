#!/usr/bin/env python3
"""
Исправляет инвертированные PARENT/CHILD из старого seed_english_expanded.py.

В API: memorial_id=A, related=B, type=PARENT  ⇒  B — родитель A.
В старых сидах для «родители → ребёнок» стояла обратная пара.

Также удаляет любые PARENT/CHILD между сиблингами:
- Sarah Elizabeth Kelly ↔ Daniel James Kelly (Kelly);
- George William Anderson ↔ Helen Margaret Anderson Kelly (Anderson, общие родители William+Agnes),
и добавляет SIBLING в обе стороны при отсутствии.

Запуск из backend/:
  python repair_expanded_family_rels.py

Дополнительно переименовывает мемориал Catherine O'Neill Kelly → Catherine Kelly (O'Neill), если есть.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import SessionLocal, engine

# При DEBUG=true в .env echo=True — для этого скрипта отключаем вывод SQL в консоль.
engine.echo = False

from app.models import FamilyRelationship, Memorial, RelationshipType


def _mid(db: Session, *names: str) -> int | None:
    for n in names:
        m = db.query(Memorial).filter(Memorial.name == n).first()
        if m:
            return m.id
    return None


def _delete_pc_between(db: Session, a: int, b: int) -> int:
    n = (
        db.query(FamilyRelationship)
        .filter(
            FamilyRelationship.memorial_id.in_((a, b)),
            FamilyRelationship.related_memorial_id.in_((a, b)),
            FamilyRelationship.relationship_type.in_(
                (RelationshipType.PARENT, RelationshipType.CHILD)
            ),
        )
        .delete(synchronize_session=False)
    )
    return n


def _add_pc(db: Session, child_id: int, parent_id: int) -> None:
    def add(a: int, b: int, t: RelationshipType) -> None:
        exists = (
            db.query(FamilyRelationship)
            .filter(
                FamilyRelationship.memorial_id == a,
                FamilyRelationship.related_memorial_id == b,
                FamilyRelationship.relationship_type == t,
            )
            .first()
        )
        if not exists:
            db.add(FamilyRelationship(memorial_id=a, related_memorial_id=b, relationship_type=t))

    add(child_id, parent_id, RelationshipType.PARENT)
    add(parent_id, child_id, RelationshipType.CHILD)


def _ensure_sibling_pair(db: Session, a: int, b: int) -> None:
    """Два направления sibling — для full-tree и раскладки «в один ряд»."""
    for x, y in ((a, b), (b, a)):
        exists = (
            db.query(FamilyRelationship)
            .filter(
                FamilyRelationship.memorial_id == x,
                FamilyRelationship.related_memorial_id == y,
                FamilyRelationship.relationship_type == RelationshipType.SIBLING,
            )
            .first()
        )
        if not exists:
            db.add(
                FamilyRelationship(
                    memorial_id=x,
                    related_memorial_id=y,
                    relationship_type=RelationshipType.SIBLING,
                )
            )
            print(f"  ✅ Added SIBLING {x} ↔ {y}")


def repair(db: Session) -> None:
    cat_new = "Catherine Kelly (O'Neill)"
    cat_old = "Catherine O'Neill Kelly"
    cm = db.query(Memorial).filter(Memorial.name == cat_old).first()
    if cm and not db.query(Memorial).filter(Memorial.name == cat_new).first():
        cm.name = cat_new
        db.flush()
        print(f"Renamed memorial: {cat_old!r} → {cat_new!r}")

    robert = _mid(db, "Robert James Kelly")
    patricia = _mid(db, "Patricia Ann Murphy Kelly")
    michael = _mid(db, "Michael Robert Kelly")
    catherine = _mid(db, cat_new, cat_old)
    sarah = _mid(db, "Sarah Elizabeth Kelly")
    daniel = _mid(db, "Daniel James Kelly")
    william = _mid(db, "William Duncan Anderson")
    agnes = _mid(db, "Agnes Brown Anderson")
    george = _mid(db, "George William Anderson")
    margaret = _mid(db, "Margaret Fraser Anderson")
    ian = _mid(db, "Ian George Anderson")

    if sarah and daniel:
        removed_sd = _delete_pc_between(db, sarah, daniel)
        if removed_sd:
            print(
                f"  🗑 Removed {removed_sd} Sarah↔Daniel parent/child row(s) "
                "(siblings must not be parent/child)"
            )
        _ensure_sibling_pair(db, sarah, daniel)

    helen = _mid(db, "Helen Margaret Anderson Kelly")
    if george and helen:
        removed_gh = _delete_pc_between(db, george, helen)
        if removed_gh:
            print(
                f"  🗑 Removed {removed_gh} George↔Helen parent/child row(s) "
                "(siblings, Anderson branch)"
            )
        _ensure_sibling_pair(db, george, helen)

    triples: list[tuple[int | None, int | None, str]] = [
        (michael, robert, "Michael ← Robert"),
        (michael, patricia, "Michael ← Patricia"),
        (sarah, michael, "Sarah ← Michael"),
        (sarah, catherine, "Sarah ← Catherine"),
        (daniel, michael, "Daniel ← Michael"),
        (daniel, catherine, "Daniel ← Catherine"),
        (george, william, "George ← William"),
        (george, agnes, "George ← Agnes"),
        (ian, george, "Ian ← George"),
        (ian, margaret, "Ian ← Margaret"),
    ]

    for child, parent, label in triples:
        if child is None or parent is None:
            print(f"  ⏭️  Skip {label}: missing memorial id")
            continue
        removed = _delete_pc_between(db, child, parent)
        if removed:
            print(f"  🗑 Removed {removed} old parent/child row(s) between {label}")
        _add_pc(db, child, parent)
        print(f"  ✅ {label}")

    db.commit()
    print("Done.")


def main() -> None:
    db = SessionLocal()
    try:
        repair(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
