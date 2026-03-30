"""
Сессия пользователя: Redis (основной) или in-memory dict (fallback).
Ключ: tg:{chat_id}
Значение: {memorial_id, voice_mode, include_family}
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

# Fallback: in-memory dict (когда Redis недоступен)
_sessions: dict[int, dict] = {}
_redis = None


async def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        _redis = client
        print("✅ Bot session: Redis connected")
    except Exception as e:
        print(f"⚠️  Bot session: Redis unavailable ({e}), using in-memory fallback")
        _redis = None
    return _redis


async def get_session(chat_id: int) -> dict | None:
    redis = await _get_redis()
    if redis:
        try:
            raw = await redis.get(f"tg:{chat_id}")
            return json.loads(raw) if raw else None
        except Exception:
            pass
    return _sessions.get(chat_id)


async def set_session(chat_id: int, data: dict) -> None:
    redis = await _get_redis()
    if redis:
        try:
            await redis.set(f"tg:{chat_id}", json.dumps(data), ex=86400 * 30)
            return
        except Exception:
            pass
    _sessions[chat_id] = data


async def clear_session(chat_id: int) -> None:
    redis = await _get_redis()
    if redis:
        try:
            await redis.delete(f"tg:{chat_id}")
        except Exception:
            pass
    _sessions.pop(chat_id, None)
