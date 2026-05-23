"""
Shared rate limiter instance for slowapi.
Imported by main.py (middleware setup) and individual route modules (decorators).
"""
from fastapi import Request
from slowapi import Limiter


def _rate_limit_key(request: Request) -> str:
    """IP-based rate limit key with X-Forwarded-For support (reverse proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_rate_limit_key)
