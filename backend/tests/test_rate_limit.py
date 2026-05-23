"""
Tests for rate limiting.

Rate limiting is bypassed in conftest._bypass_rate_limit for all normal tests.
This file tests rate limit enforcement at the key-function and limits-storage level.
"""
import pytest
from unittest.mock import MagicMock

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from limits import parse_many, parse
from limits.strategies import MovingWindowRateLimiter
from limits.storage import MemoryStorage


# ── Key function tests ──────────────────────────────────────────────────────


def _mock_request(ip: str = "127.0.0.1") -> MagicMock:
    req = MagicMock()
    req.client.host = ip
    req.headers = {}
    return req


def _mock_request_with_forwarded(ip: str) -> MagicMock:
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = "internal"
    req.headers = {"X-Forwarded-For": ip}
    return req


class TestRateLimitKeyFunction:
    """IP- extracting  key function from app.limiter."""

    def test_key_from_client_ip(self):
        from app.limiter import _rate_limit_key
        assert _rate_limit_key(_mock_request("1.2.3.4")) == "1.2.3.4"

    def test_key_from_x_forwarded_for(self):
        from app.limiter import _rate_limit_key
        assert _rate_limit_key(_mock_request_with_forwarded("5.6.7.8")) == "5.6.7.8"

    def test_key_x_forwarded_for_multiple_ips(self):
        from app.limiter import _rate_limit_key
        assert _rate_limit_key(_mock_request_with_forwarded("10.0.0.1, 10.0.0.2, 10.0.0.3")) == "10.0.0.1"

    def test_key_fallback_when_no_client(self):
        from app.limiter import _rate_limit_key
        req = MagicMock()
        req.client = None
        req.headers = {}
        assert _rate_limit_key(req) == "unknown"


# ── Limits-storage tests ────────────────────────────────────────────────────


class TestRateLimitEnforcement:
    """Rate limit enforcement via limits library (MovingWindowRateLimiter + MemoryStorage)."""

    def test_under_limit_passes(self):
        strategy = MovingWindowRateLimiter(MemoryStorage())
        assert strategy.hit(parse("100/minute"), "key", "100/minute") is True

    def test_limit_blocks_excess(self):
        strategy = MovingWindowRateLimiter(MemoryStorage())
        limit = parse("2/minute")
        key = "ip:/path"
        assert strategy.hit(limit, key, "2/minute") is True
        assert strategy.hit(limit, key, "2/minute") is True
        assert strategy.hit(limit, key, "2/minute") is False

    def test_different_ips_independent(self):
        strategy = MovingWindowRateLimiter(MemoryStorage())
        limit = parse("2/minute")
        assert strategy.hit(limit, "1.1.1.1", "2/minute") is True
        assert strategy.hit(limit, "1.1.1.1", "2/minute") is True
        assert strategy.hit(limit, "1.1.1.1", "2/minute") is False

        # Different IP — fresh
        assert strategy.hit(limit, "2.2.2.2", "2/minute") is True

    def test_different_endpoints_independent(self):
        strategy = MovingWindowRateLimiter(MemoryStorage())
        limit = parse("2/minute")
        login = "1.2.3.4:/api/v1/auth/login"
        register = "1.2.3.4:/api/v1/auth/register"

        assert strategy.hit(limit, login, "2/minute") is True
        assert strategy.hit(limit, login, "2/minute") is True
        assert strategy.hit(limit, login, "2/minute") is False

        # Different endpoint — fresh
        assert strategy.hit(limit, register, "2/minute") is True

    def test_auth_endpoint_allows_10_per_minute(self):
        """Auth limit of 10/minute: 10 pass, 11th blocked."""
        strategy = MovingWindowRateLimiter(MemoryStorage())
        limit = parse("10/minute")
        key = "ip:/api/v1/auth/login"

        for i in range(10):
            assert strategy.hit(limit, key, "10/minute") is True, f"Hit {i+1} failed"

        assert strategy.hit(limit, key, "10/minute") is False

    def test_global_limit_200_per_minute(self):
        """Global 200/minute: 200 pass, 201st blocked."""
        strategy = MovingWindowRateLimiter(MemoryStorage())
        limit = parse("200/minute")
        key = "ip:/*"

        for i in range(200):
            assert strategy.hit(limit, key, "200/minute") is True, f"Hit {i+1} failed"

        assert strategy.hit(limit, key, "200/minute") is False

