"""
HTTP-клиент к локальному FastAPI.
Бот обращается к API через HTTP — не импортирует модели напрямую.
"""
import httpx
import sys
import os

# Добавляем путь к backend, чтобы импортировать config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

BASE = settings.BOT_API_BASE_URL


async def get_memorials() -> list[dict]:
    """Получить список всех мемориалов."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/memorials/")
        r.raise_for_status()
        return r.json()


async def get_memorial(memorial_id: int) -> dict | None:
    """Получить один мемориал по ID."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/memorials/{memorial_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def avatar_chat(
    memorial_id: int,
    question: str,
    include_audio: bool,
    include_family: bool,
) -> dict:
    """
    Отправить вопрос аватару и получить ответ.
    Возвращает: {answer, audio_url, sources, ...}
    """
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{BASE}/ai/avatar/chat", json={
            "memorial_id": memorial_id,
            "question": question,
            "include_audio": include_audio,
            "include_family_memories": include_family,
            "use_persona": True,
        })
        r.raise_for_status()
        return r.json()


def build_audio_url(audio_url: str) -> str:
    """
    Превращает относительный audio_url в абсолютный.
    /api/v1/media/audio/file.mp3 → http://localhost:8000/api/v1/media/audio/file.mp3
    Если задан PUBLIC_API_URL (ngrok), использует его.
    """
    if audio_url.startswith("http"):
        return audio_url
    base = settings.PUBLIC_API_URL or settings.BOT_API_BASE_URL.removesuffix("/api/v1")
    return f"{base}{audio_url}"
