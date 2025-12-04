"""
Health check endpoint.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health/")
async def health_check():
    """
    Проверка работоспособности сервиса.
    """
    return {"status": "ok", "service": "memorial-mvp"}

