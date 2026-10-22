"""Short-lived playback links for private, owner-provided audio replies."""
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings

AUDIENCE = 'saved-memory-audio'


def recorded_reply_url(memory_id):
    token = jwt.encode({
        'memory_id': memory_id, 'aud': AUDIENCE,
        'exp': datetime.now(timezone.utc) + timedelta(hours=12),
    }, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return f'/api/v1/ai/recorded-reply/{memory_id}?token={token}'
