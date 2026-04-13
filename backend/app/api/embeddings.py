"""
API endpoints для управления embeddings воспоминаний.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import settings
from app.db import get_db
from app.models import Memory, Memorial
from app.services.ai_tasks import (
    get_embedding,
    upsert_memory_embedding,
    delete_memory_embedding,
)
from app.workers.worker import create_memory_embedding_task
from app.schemas import MemoryResponse

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


def _require_admin_key(x_admin_key: Optional[str] = Header(default=None)):
    """Simple admin key check for maintenance endpoints."""
    if not x_admin_key or x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Admin key required")


@router.post("/admin/rebuild-all")
async def admin_rebuild_all_embeddings(
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin_key),
):
    """
    Admin: пересоздать embeddings для ВСЕХ воспоминаний всех мемориалов.
    Защищён заголовком X-Admin-Key: <SECRET_KEY>.
    """
    memories = db.query(Memory).all()
    ok = 0
    failed = 0
    results = []

    for memory in memories:
        try:
            embedding = await get_embedding(memory.content)
            embedding_id = await upsert_memory_embedding(
                memory_id=memory.id,
                memorial_id=memory.memorial_id,
                embedding=embedding,
                text=memory.content,
            )
            if embedding_id:
                memory.embedding_id = embedding_id
                ok += 1
            else:
                failed += 1
                results.append({"memory_id": memory.id, "status": "upsert_none"})
        except Exception as e:
            failed += 1
            results.append({"memory_id": memory.id, "status": "error", "detail": str(e)})

    db.commit()
    return {
        "total": len(memories),
        "ok": ok,
        "failed": failed,
        "errors": results,
    }


@router.post("/memories/{memory_id}/recreate")
async def recreate_memory_embedding(
    memory_id: int,
    db: Session = Depends(get_db),
):
    """
    Пересоздать embedding для воспоминания.
    Полезно если embedding был удален или нужно обновить.
    """
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Запускаем задачу в фоне
    task = create_memory_embedding_task.delay(
        memory_id=memory_id,
        memorial_id=memory.memorial_id,
        text=memory.content
    )
    
    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Embedding recreation task queued"
    }


@router.post("/memorials/{memorial_id}/recreate-all")
async def recreate_all_memorial_embeddings(
    memorial_id: int,
    db: Session = Depends(get_db),
):
    """
    Пересоздать embeddings для всех воспоминаний мемориала.
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    memories = db.query(Memory).filter(Memory.memorial_id == memorial_id).all()
    
    task_ids = []
    for memory in memories:
        task = create_memory_embedding_task.delay(
            memory_id=memory.id,
            memorial_id=memorial_id,
            text=memory.content
        )
        task_ids.append(task.id)
    
    return {
        "status": "queued",
        "memorial_id": memorial_id,
        "memories_count": len(memories),
        "task_ids": task_ids,
        "message": f"Queued {len(memories)} embedding recreation tasks"
    }


@router.delete("/memories/{memory_id}")
async def delete_memory_embedding_endpoint(
    memory_id: int,
    db: Session = Depends(get_db),
):
    """
    Удалить embedding воспоминания из Pinecone.
    Само воспоминание в БД не удаляется.
    """
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    if not memory.embedding_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Memory has no embedding"
        )
    
    success = await delete_memory_embedding(memory_id, memory.memorial_id)
    
    if success:
        # Очищаем embedding_id в БД
        memory.embedding_id = None
        db.commit()
        
        return {
            "status": "deleted",
            "message": "Embedding deleted successfully"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete embedding"
        )


@router.get("/memorials/{memorial_id}/status")
async def get_embeddings_status(
    memorial_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить статус embeddings для мемориала.
    Показывает сколько воспоминаний имеют embeddings.
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    memories = db.query(Memory).filter(Memory.memorial_id == memorial_id).all()
    
    total = len(memories)
    with_embeddings = sum(1 for m in memories if m.embedding_id)
    without_embeddings = total - with_embeddings
    
    return {
        "memorial_id": memorial_id,
        "total_memories": total,
        "with_embeddings": with_embeddings,
        "without_embeddings": without_embeddings,
        "coverage_percent": round((with_embeddings / total * 100) if total > 0 else 0, 2)
    }

