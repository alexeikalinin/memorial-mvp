"""
Unit-тесты биллинг-сервиса: лимиты, квоты, тарифные планы.

Важно: conftest._bypass_billing отключает проверки глобально.
Этот файл переопределяет его пустой фикстурой, чтобы тестировать
реальную логику billing.py.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.services.billing import (
    check_memorial_limit,
    check_chat_quota,
    check_animation_quota,
    check_tts_access,
    check_family_rag_access,
    check_live_session_quota,
    increment_chat_usage,
    increment_animation_usage,
    increment_live_session_usage,
    get_limits,
    _effective_plan,
    PLAN_LIMITS,
)
from app.models import User, UserUsage, MemorialAccess, UserRole


# ── Переопределяем autouse-фикстуру conftest — здесь тестируем биллинг как он есть ──

@pytest.fixture(autouse=True)
def _bypass_billing():
    """Не отключаем биллинг в этом модуле — мы его тестируем."""
    yield


# ── Вспомогательные фабрики ────────────────────────────────────────────────────

def _make_user(
    plan="free",
    is_demo=False,
    expires_at=None,
    extra_memorials=0,
    live_sessions_remaining=0,
    lifetime_memorial_id=None,
    user_id=99,
):
    u = MagicMock(spec=User)
    u.id = user_id
    u.subscription_plan = plan
    u.is_demo = is_demo
    u.plan_expires_at = expires_at
    u.extra_memorials = extra_memorials
    u.live_sessions_remaining = live_sessions_remaining
    u.lifetime_memorial_id = lifetime_memorial_id
    return u


def _make_db_with_usage(user_id, period, chat=0, animations=0, live=0):
    """Возвращает mock-сессию, которая отдаёт нужный UserUsage."""
    usage = UserUsage(
        user_id=user_id,
        period=period,
        chat_messages=chat,
        animations=animations,
        live_sessions=live,
    )
    usage.id = 1

    db = MagicMock()
    query_mock = db.query.return_value
    filter_mock = query_mock.filter.return_value
    filter_mock.first.return_value = usage
    db.commit = MagicMock()
    db.add = MagicMock()
    db.refresh = MagicMock()
    return db, usage


def _make_db_no_usage():
    """DB без записи UserUsage — будет создан новый."""
    db = MagicMock()
    query_mock = db.query.return_value
    filter_mock = query_mock.filter.return_value
    filter_mock.first.return_value = None
    db.commit = MagicMock()
    db.add = MagicMock()
    db.refresh = MagicMock()
    return db


# ── _effective_plan ────────────────────────────────────────────────────────────

def test_effective_plan_free():
    u = _make_user(plan="free")
    assert _effective_plan(u) == "free"


def test_effective_plan_plus_active():
    future = datetime.now(timezone.utc) + timedelta(days=30)
    u = _make_user(plan="plus", expires_at=future)
    assert _effective_plan(u) == "plus"


def test_effective_plan_plus_expired():
    """Истёкшая подписка плюс → free."""
    past = datetime.now(timezone.utc) - timedelta(days=1)
    u = _make_user(plan="plus", expires_at=past)
    assert _effective_plan(u) == "free"


def test_effective_plan_lifetime_no_expiry():
    """Lifetime — без expires_at, должен оставаться lifetime."""
    u = _make_user(plan="lifetime", expires_at=None)
    assert _effective_plan(u) == "lifetime"


def test_effective_plan_pro_expired():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    u = _make_user(plan="pro", expires_at=past)
    assert _effective_plan(u) == "free"


# ── check_memorial_limit ───────────────────────────────────────────────────────

def _db_with_memorial_count(count, user_id=99):
    """DB, где у пользователя ровно `count` мемориалов с ролью OWNER."""
    db = MagicMock()
    q = db.query.return_value.filter.return_value
    q.count.return_value = count
    return db


def test_memorial_limit_free_zero_ok():
    u = _make_user(plan="free")
    db = _db_with_memorial_count(0)
    check_memorial_limit(u, db)  # не бросает


def test_memorial_limit_free_one_blocked():
    u = _make_user(plan="free")
    db = _db_with_memorial_count(1)
    with pytest.raises(HTTPException) as exc:
        check_memorial_limit(u, db)
    assert exc.value.status_code == 402


def test_memorial_limit_plus_nine_ok():
    u = _make_user(plan="plus")
    db = _db_with_memorial_count(9)
    check_memorial_limit(u, db)


def test_memorial_limit_plus_ten_blocked():
    u = _make_user(plan="plus")
    db = _db_with_memorial_count(10)
    with pytest.raises(HTTPException) as exc:
        check_memorial_limit(u, db)
    assert exc.value.status_code == 402


def test_memorial_limit_plus_extra_slots():
    """Plus + 2 extra слота → лимит 12."""
    u = _make_user(plan="plus", extra_memorials=2)
    db = _db_with_memorial_count(11)
    check_memorial_limit(u, db)  # 11 < 12 — ок

    db2 = _db_with_memorial_count(12)
    with pytest.raises(HTTPException):
        check_memorial_limit(u, db2)


def test_memorial_limit_demo_bypass():
    """Демо-аккаунт не проверяет лимит."""
    u = _make_user(plan="free", is_demo=True)
    db = _db_with_memorial_count(1000)
    check_memorial_limit(u, db)  # не бросает


# ── check_chat_quota ──────────────────────────────────────────────────────────

def test_chat_quota_free_ok(db_session):
    """Free: первые 15 сообщений — ok."""
    from app.services.billing import _current_period
    u = _make_user()
    db, usage = _make_db_with_usage(99, _current_period(), chat=14)
    check_chat_quota(u, memorial_id=1, db=db)  # 14 < 15 — ок


def test_chat_quota_free_exhausted():
    from app.services.billing import _current_period
    u = _make_user()
    db, usage = _make_db_with_usage(99, _current_period(), chat=15)
    with pytest.raises(HTTPException) as exc:
        check_chat_quota(u, memorial_id=1, db=db)
    assert exc.value.status_code == 402


def test_chat_quota_plus_200():
    from app.services.billing import _current_period
    u = _make_user(plan="plus")
    db, usage = _make_db_with_usage(99, _current_period(), chat=200)
    with pytest.raises(HTTPException):
        check_chat_quota(u, memorial_id=1, db=db)

    db2, _ = _make_db_with_usage(99, _current_period(), chat=199)
    check_chat_quota(u, memorial_id=1, db=db2)  # 199 < 200 — ок


def test_chat_quota_demo_bypass():
    from app.services.billing import _current_period
    u = _make_user(plan="free", is_demo=True)
    db, _ = _make_db_with_usage(99, _current_period(), chat=9999)
    check_chat_quota(u, memorial_id=1, db=db)


def test_chat_quota_lifetime_wrong_memorial():
    """Lifetime план: чат только на locked memorial."""
    from app.services.billing import _current_period
    u = _make_user(plan="lifetime", lifetime_memorial_id=42)
    db, _ = _make_db_with_usage(99, _current_period(), chat=0)
    with pytest.raises(HTTPException) as exc:
        check_chat_quota(u, memorial_id=99, db=db)  # не тот мемориал
    assert exc.value.status_code == 402


def test_chat_quota_lifetime_correct_memorial():
    from app.services.billing import _current_period
    u = _make_user(plan="lifetime", lifetime_memorial_id=42)
    db, _ = _make_db_with_usage(99, _current_period(), chat=0)
    check_chat_quota(u, memorial_id=42, db=db)  # правильный — ок


# ── check_animation_quota ─────────────────────────────────────────────────────

def test_animation_free_blocked():
    """Free: анимации вообще нет."""
    u = _make_user(plan="free")
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        check_animation_quota(u, db)
    assert exc.value.status_code == 402


def test_animation_plus_ok():
    from app.services.billing import _current_period
    u = _make_user(plan="plus")
    db, _ = _make_db_with_usage(99, _current_period(), animations=4)
    check_animation_quota(u, db)  # 4 < 5 — ок


def test_animation_plus_exhausted():
    from app.services.billing import _current_period
    u = _make_user(plan="plus")
    db, _ = _make_db_with_usage(99, _current_period(), animations=5)
    with pytest.raises(HTTPException) as exc:
        check_animation_quota(u, db)
    assert exc.value.status_code == 402


def test_animation_pro_15():
    from app.services.billing import _current_period
    u = _make_user(plan="pro")
    db, _ = _make_db_with_usage(99, _current_period(), animations=14)
    check_animation_quota(u, db)  # 14 < 15 — ок

    db2, _ = _make_db_with_usage(99, _current_period(), animations=15)
    with pytest.raises(HTTPException):
        check_animation_quota(u, db2)


def test_animation_demo_bypass():
    u = _make_user(plan="free", is_demo=True)
    db = MagicMock()
    check_animation_quota(u, db)  # не бросает


# ── check_tts_access ──────────────────────────────────────────────────────────

def test_tts_free_blocked():
    u = _make_user(plan="free")
    with pytest.raises(HTTPException) as exc:
        check_tts_access(u)
    assert exc.value.status_code == 402


def test_tts_plus_ok():
    u = _make_user(plan="plus")
    check_tts_access(u)  # не бросает


def test_tts_pro_ok():
    u = _make_user(plan="pro")
    check_tts_access(u)


def test_tts_lifetime_ok():
    u = _make_user(plan="lifetime")
    check_tts_access(u)


def test_tts_demo_bypass():
    u = _make_user(plan="free", is_demo=True)
    check_tts_access(u)


# ── check_family_rag_access ───────────────────────────────────────────────────

def test_family_rag_free_blocked():
    u = _make_user(plan="free")
    with pytest.raises(HTTPException) as exc:
        check_family_rag_access(u)
    assert exc.value.status_code == 402


def test_family_rag_lifetime_blocked():
    """Lifetime — family RAG недоступен."""
    u = _make_user(plan="lifetime")
    with pytest.raises(HTTPException):
        check_family_rag_access(u)


def test_family_rag_plus_ok():
    u = _make_user(plan="plus")
    check_family_rag_access(u)


def test_family_rag_pro_ok():
    u = _make_user(plan="pro")
    check_family_rag_access(u)


def test_family_rag_demo_bypass():
    u = _make_user(plan="free", is_demo=True)
    check_family_rag_access(u)


# ── check_live_session_quota ──────────────────────────────────────────────────

def test_live_session_free_blocked():
    u = _make_user(plan="free")
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        check_live_session_quota(u, db)
    assert exc.value.status_code == 402


def test_live_session_plus_blocked():
    """Plus — live avatar недоступен."""
    u = _make_user(plan="plus")
    db = MagicMock()
    with pytest.raises(HTTPException):
        check_live_session_quota(u, db)


def test_live_session_pro_ok():
    from app.services.billing import _current_period
    u = _make_user(plan="pro")
    db, _ = _make_db_with_usage(99, _current_period(), live=4)
    check_live_session_quota(u, db)  # 4 < 5 — ок


def test_live_session_pro_exhausted():
    from app.services.billing import _current_period
    u = _make_user(plan="pro")
    db, _ = _make_db_with_usage(99, _current_period(), live=5)
    with pytest.raises(HTTPException) as exc:
        check_live_session_quota(u, db)
    assert exc.value.status_code == 402


def test_live_session_lifetime_pro_pool_ok():
    """Lifetime Pro: использует pool, не месячный счётчик."""
    u = _make_user(plan="lifetime_pro", live_sessions_remaining=3)
    db = MagicMock()
    check_live_session_quota(u, db)  # 3 > 0 — ок


def test_live_session_lifetime_pro_pool_empty():
    u = _make_user(plan="lifetime_pro", live_sessions_remaining=0)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        check_live_session_quota(u, db)
    assert exc.value.status_code == 402


def test_live_session_demo_bypass():
    u = _make_user(plan="free", is_demo=True)
    db = MagicMock()
    check_live_session_quota(u, db)


# ── Инкременты ────────────────────────────────────────────────────────────────

def test_increment_chat_usage():
    from app.services.billing import _current_period
    u = _make_user()
    db, usage = _make_db_with_usage(99, _current_period(), chat=5)
    increment_chat_usage(u, db)
    assert usage.chat_messages == 6
    db.commit.assert_called()


def test_increment_animation_usage():
    from app.services.billing import _current_period
    u = _make_user(plan="plus")
    db, usage = _make_db_with_usage(99, _current_period(), animations=2)
    increment_animation_usage(u, db)
    assert usage.animations == 3


def test_increment_live_session_pro():
    from app.services.billing import _current_period
    u = _make_user(plan="pro")
    db, usage = _make_db_with_usage(99, _current_period(), live=1)
    increment_live_session_usage(u, db)
    assert usage.live_sessions == 2


def test_increment_live_session_lifetime_pro_decrements_pool():
    u = _make_user(plan="lifetime_pro", live_sessions_remaining=5)
    db = MagicMock()
    db.commit = MagicMock()
    increment_live_session_usage(u, db)
    assert u.live_sessions_remaining == 4
    db.commit.assert_called()


# ── HTTP-level: лимит мемориалов через API ────────────────────────────────────

def test_memorial_limit_via_api_free_plan(client, auth_headers):
    """Free-план: первый мемориал создаётся, второй → 402."""
    # Первый — ок
    r1 = client.post(
        "/api/v1/memorials/",
        json={"name": "Первый"},
        headers=auth_headers,
    )
    assert r1.status_code == 201

    # Второй — 402
    r2 = client.post(
        "/api/v1/memorials/",
        json={"name": "Второй"},
        headers=auth_headers,
    )
    assert r2.status_code == 402
    assert "402" in str(r2.status_code)
