"""
Billing service — plan limits and quota enforcement.

Plans:
  free         — 1 memorial, 15 chat/mo, no TTS, no animation, no live avatar, no family RAG
  plus         — 10 memorials (+add-ons), 200 chat/mo, TTS, 5 animations/mo, family RAG, no live avatar
  pro          — 10 memorials (+add-ons), 500 chat/mo, TTS, 15 animations/mo, family RAG, 5 live sessions/mo (+add-ons)
  lifetime     — 1 locked memorial, 200 chat/mo, TTS, 5 animations/mo, no live avatar, no family RAG
  lifetime_pro — 1 locked memorial, 200 chat/mo, TTS, 15 animations/mo, pool of 100 live sessions (pre-paid, never resets)

Add-ons (stored on User):
  extra_memorials        — additional memorial slots bought on top of plan limit (plus/pro only)
  live_sessions_remaining — pre-paid session pool for lifetime_pro; decremented on each session
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Memorial, MemorialAccess, User, UserRole, UserUsage

# ─── Plan definitions ─────────────────────────────────────────────────────────

PLAN_LIMITS: dict = {
    "free": {
        "memorials": 1,
        "chat_messages_per_month": 15,
        "animations_per_month": 0,
        "tts_enabled": False,
        "family_rag": False,
        "live_sessions_per_month": 0,   # no live avatar
        "live_session_pool": False,      # pool model (lifetime_pro)
        "extra_memorials_allowed": False,
        "storage_mb": 500,
    },
    "plus": {
        "memorials": 10,
        "chat_messages_per_month": 200,
        "animations_per_month": 5,
        "tts_enabled": True,
        "family_rag": True,
        "live_sessions_per_month": 0,   # live avatar not included; upgrade to Pro
        "live_session_pool": False,
        "extra_memorials_allowed": True,
        "storage_mb": 5120,             # 5 GB
    },
    "pro": {
        "memorials": 10,
        "chat_messages_per_month": 500,
        "animations_per_month": 15,
        "tts_enabled": True,
        "family_rag": True,
        "live_sessions_per_month": 5,   # 5 included/month; add-on packs available
        "live_session_pool": False,
        "extra_memorials_allowed": True,
        "storage_mb": 15360,            # 15 GB
    },
    "lifetime": {
        "memorials": 1,                 # single locked memorial
        "chat_messages_per_month": 200,
        "animations_per_month": 5,
        "tts_enabled": True,
        "family_rag": False,
        "live_sessions_per_month": 0,   # no live avatar; upgrade to Lifetime Pro
        "live_session_pool": False,
        "extra_memorials_allowed": False,
        "storage_mb": 5120,             # 5 GB
    },
    "lifetime_pro": {
        "memorials": 1,                 # single locked memorial
        "chat_messages_per_month": 200,
        "animations_per_month": 15,
        "tts_enabled": True,
        "family_rag": False,
        "live_sessions_per_month": 0,   # uses pool model instead of monthly counter
        "live_session_pool": True,      # draws from user.live_sessions_remaining
        "extra_memorials_allowed": False,
        "storage_mb": 10240,            # 10 GB
    },
}

UPGRADE_URL = "/#pricing"  # sent in 402 response detail


def _current_period() -> str:
    """Returns current billing period as 'YYYY-MM' (UTC)."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m")


def _effective_plan(user: User) -> str:
    """
    Returns the user's active plan string.
    Falls back to 'free' if plan_expires_at is set and in the past (plus/pro subscriptions).
    """
    plan = user.subscription_plan or "free"
    if plan in ("plus", "pro") and user.plan_expires_at:
        if datetime.now(timezone.utc) > user.plan_expires_at:
            return "free"
    return plan


def get_limits(user: User) -> dict:
    """Returns the limit dict for the user's effective plan."""
    return PLAN_LIMITS.get(_effective_plan(user), PLAN_LIMITS["free"])


def _get_or_create_usage(user_id: int, db: Session) -> "UserUsage":
    """Fetches (or creates) the UserUsage row for the current billing period."""
    period = _current_period()
    usage = (
        db.query(UserUsage)
        .filter(UserUsage.user_id == user_id, UserUsage.period == period)
        .first()
    )
    if not usage:
        usage = UserUsage(user_id=user_id, period=period, chat_messages=0, animations=0)
        db.add(usage)
        db.commit()
        db.refresh(usage)
    return usage


# ─── Helpers ──────────────────────────────────────────────────────────────────

def is_demo_account(user: User) -> bool:
    """Demo/seed accounts and global admins bypass all billing checks."""
    if getattr(user, "is_demo", False):
        return True
    from app.auth import is_global_admin
    return is_global_admin(user)


# ─── Guards ───────────────────────────────────────────────────────────────────

def check_memorial_limit(user: User, db: Session) -> None:
    """
    Raises HTTP 402 if the user has reached their memorial count limit.
    Call before creating a new memorial.
    """
    if is_demo_account(user):
        return
    limits = get_limits(user)
    base_limit = limits["memorials"]
    extra = user.extra_memorials if limits.get("extra_memorials_allowed") else 0
    max_memorials = base_limit + extra

    # Count owned memorials
    owned = (
        db.query(MemorialAccess)
        .filter(
            MemorialAccess.user_id == user.id,
            MemorialAccess.role == UserRole.OWNER,
        )
        .count()
    )
    if owned >= max_memorials:
        plan = _effective_plan(user)
        if plan == "free":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Free plan allows {base_limit} memorial(s). "
                    f"Upgrade to Plus to create up to 10 memorials. {UPGRADE_URL}"
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Your plan allows a maximum of {max_memorials} memorial(s) "
                f"({base_limit} base + {extra} add-on). "
                f"Purchase additional memorial slots or upgrade your plan."
            ),
        )


def check_chat_quota(user: User, memorial_id: int, db: Session) -> None:
    """
    Raises HTTP 402 if the user has exhausted their monthly chat quota.
    For lifetime plan, only allows chat on the locked memorial.
    Call before processing an avatar chat request.
    """
    if is_demo_account(user):
        return
    plan = _effective_plan(user)
    limits = get_limits(user)
    max_msgs = limits["chat_messages_per_month"]

    # Lifetime: only the locked memorial is allowed
    if plan == "lifetime":
        if user.lifetime_memorial_id and user.lifetime_memorial_id != memorial_id:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    "Your Lifetime plan is locked to a specific memorial. "
                    "Upgrade to Plus for access to all your memorials."
                ),
            )

    usage = _get_or_create_usage(user.id, db)
    if usage.chat_messages >= max_msgs:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"You've used all {max_msgs} chat messages for this month "
                f"(plan: {plan}). Resets on the 1st. "
                + (f"Upgrade to Plus for 200 messages/month. {UPGRADE_URL}" if plan == "free" else "")
            ),
        )


def increment_chat_usage(user: User, db: Session) -> None:
    """Increments the chat message counter for the current period."""
    usage = _get_or_create_usage(user.id, db)
    usage.chat_messages += 1
    db.commit()


def check_animation_quota(user: User, db: Session) -> None:
    """
    Raises HTTP 402 if the user cannot use photo animation (quota or plan limit).
    Call before starting an animation task.
    """
    if is_demo_account(user):
        return
    limits = get_limits(user)
    max_renders = limits["animations_per_month"]

    if max_renders == 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Photo animation is not available on the Free plan. "
                f"Upgrade to Plus or purchase a Lifetime memorial. {UPGRADE_URL}"
            ),
        )

    usage = _get_or_create_usage(user.id, db)
    if usage.animations >= max_renders:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"You've used all {max_renders} animation render(s) for this month. "
                "Resets on the 1st."
            ),
        )


def increment_animation_usage(user: User, db: Session) -> None:
    """Increments the animation counter for the current period."""
    usage = _get_or_create_usage(user.id, db)
    usage.animations += 1
    db.commit()


def check_tts_access(user: User) -> None:
    """
    Raises HTTP 402 if the user's plan does not include TTS / voice cloning.
    Call before generating ElevenLabs audio or uploading a voice sample.
    """
    if is_demo_account(user):
        return
    limits = get_limits(user)
    if not limits["tts_enabled"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Voice cloning and TTS replies are not available on the Free plan. "
                f"Upgrade to Plus or Lifetime memorial. {UPGRADE_URL}"
            ),
        )


def check_family_rag_access(user: User) -> None:
    """
    Raises HTTP 402 if the user's plan does not include Family RAG.
    Call before executing a cross-memorial search.
    """
    if is_demo_account(user):
        return
    limits = get_limits(user)
    if not limits["family_rag"]:
        plan = _effective_plan(user)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Family RAG (chat across linked memorials) is a Plus/Pro feature. "
                + (f"Upgrade to Plus or Pro. {UPGRADE_URL}" if plan not in ("plus", "pro") else "")
            ),
        )


def check_live_session_quota(user: User, db: Session) -> None:
    """
    Raises HTTP 402 if the user cannot start a live avatar session.

    - Pro: up to live_sessions_per_month/month (monthly counter in UserUsage)
    - Lifetime Pro: draws from user.live_sessions_remaining pool (never resets)
    - All other plans: live avatar not available
    Call before starting a live avatar session.
    """
    if is_demo_account(user):
        return
    plan = _effective_plan(user)
    limits = get_limits(user)
    monthly_limit = limits.get("live_sessions_per_month", 0)
    uses_pool = limits.get("live_session_pool", False)

    if uses_pool:
        # Lifetime Pro: deduct from pre-paid pool
        remaining = user.live_sessions_remaining or 0
        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    "You have no live avatar sessions remaining in your pool. "
                    f"Purchase additional sessions. {UPGRADE_URL}"
                ),
            )
        return

    if monthly_limit == 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Live avatar sessions are available on Pro and Lifetime Pro plans. "
                f"Upgrade to Pro for 5 sessions/month. {UPGRADE_URL}"
            ),
        )

    usage = _get_or_create_usage(user.id, db)
    if usage.live_sessions >= monthly_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"You've used all {monthly_limit} live avatar session(s) for this month "
                f"(plan: {plan}). Resets on the 1st. "
                f"Upgrade to Lifetime Pro for a pre-paid session pool."
            ),
        )


def increment_live_session_usage(user: User, db: Session) -> None:
    """
    Increments or decrements the live session counter after a session starts.
    - Pro: increments UserUsage.live_sessions for current period
    - Lifetime Pro: decrements user.live_sessions_remaining
    """
    limits = get_limits(user)
    uses_pool = limits.get("live_session_pool", False)

    if uses_pool:
        remaining = user.live_sessions_remaining or 0
        user.live_sessions_remaining = max(0, remaining - 1)
        db.commit()
        return

    usage = _get_or_create_usage(user.id, db)
    usage.live_sessions += 1
    db.commit()
