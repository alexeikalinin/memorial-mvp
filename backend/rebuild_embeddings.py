"""
One-shot script: rebuild all embeddings for all memorials.
Run via: railway run python rebuild_embeddings.py
Or locally: cd backend && source .venv/bin/activate && python rebuild_embeddings.py
"""
import asyncio
import sys
from sqlalchemy.orm import Session

from app.db import engine, SessionLocal
from app.models import Memory, Memorial
from app.services.ai_tasks import get_embedding, upsert_memory_embedding


async def rebuild_all():
    db: Session = SessionLocal()
    try:
        memorials = db.query(Memorial).all()
        print(f"Found {len(memorials)} memorials")

        total_ok = 0
        total_fail = 0

        for memorial in memorials:
            memories = db.query(Memory).filter(Memory.memorial_id == memorial.id).all()
            if not memories:
                continue

            print(f"\n[{memorial.id}] {memorial.name} — {len(memories)} memories")
            for memory in memories:
                try:
                    embedding = await get_embedding(memory.content)
                    embedding_id = await upsert_memory_embedding(
                        memory_id=memory.id,
                        memorial_id=memorial.id,
                        embedding=embedding,
                        text=memory.content,
                    )
                    if embedding_id:
                        memory.embedding_id = embedding_id
                        db.commit()
                        total_ok += 1
                        print(f"  ✓ memory {memory.id}")
                    else:
                        total_fail += 1
                        print(f"  ✗ memory {memory.id} — upsert returned None")
                except Exception as e:
                    total_fail += 1
                    print(f"  ✗ memory {memory.id} — {e}")

        print(f"\n=== Done: {total_ok} ok, {total_fail} failed ===")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(rebuild_all())
