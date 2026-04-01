"""Ensure User id=1 exists for English seed scripts (same idea as seed_extended.py)."""
from app.models import User


def ensure_owner_user_id_1(db):
    owner = db.query(User).filter(User.id == 1).first()
    if owner:
        return owner
    owner = User(
        id=1,
        email="en-demo@memorial.local",
        username="en_demo_seed",
        hashed_password="x",
        full_name="EN demo seed owner",
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    print("✅ Created seed owner user id=1 (en-demo@memorial.local)")
    return owner
