"""
Billing service — plan limits and quota enforcement.

Plans (Variant C):
  free     — 1 memorial, 15 chat msg/month, no TTS, no animation, no family RAG
  plus     — 10 memorials, 200 chat msg/month, TTS, 5 animations/month, family RAG
  lifetime — 1 locked memorial, 200 chat msg/month, TTS, 5 animations/month, no family RAG
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
        "storage_mb": 500,
    },
    "plus": {
        "memorials": 10,
        "chat_messages_per_month": 200,
        "animations_per_month": 5,
        "tts_enabled": True,
        "family_rag": True,
        "storage_mb": 5120,  # 5 GB
    },
    "lifetime": {
        "memorials": 1,  # single locked memorial
        "chat_messages_per_month": 200,
        "animations_per_month": 5,
        "tts_enabled": True,
        "family_rag": False,
        "storage_mb": 5120,  # 5 GB
    },
}

UPGRADE_URL = "/app/pricing"  # sent in 402 response detail


def _current_period() -> str:
    """Returns current billing period as 'YYYY-MM' (UTC)."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m")


def _effective_plan(user: User) -> str:
    """
    Returns the user's active plan string.
    Falls back to 'free' if plan_expires_at is set and in the past.
    """
    plan = user.subscription_plan or "free"
    if plan == "plus" and user.plan_expires_at:
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


# ─── Guards ───────────────────────────────────────────────────────────────────

def check_memorial_limit(user: User, db: Session) -> None:
    """
    Raises HTTP 402 if the user has reached their memorial count limit.
    Call before creating a new memorial.
    """
    limits = get_limits(user)
    max_memorials = limits["memorials"]

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
                    f"Free plan allows {max_memorials} memorial(s). "
                    f"Upgrade to Plus to create up to 10 memorials. {UPGRADE_URL}"
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Your plan allows a maximum of {max_memorials} memorial(s). "
                f"You have reached this limit."
            ),
        )


def check_chat_quota(user: User, memorial_id: int, db: Session) -> None:
    """
    Raises HTTP 402 if the user has exhausted their monthly chat quota.
    For lifetime plan, only allows chat on the locked memorial.
    Call before processing an avatar chat request.
    """
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
    limits = get_limits(user)
    if not limits["family_rag"]:
        plan = _effective_plan(user)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Family RAG (chat across linked memorials) is a Plus-only feature. "
                + (f"Upgrade to Plus. {UPGRADE_URL}" if plan != "plus" else "")
            ),
        )
