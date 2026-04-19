"""
Billing API: Stripe Checkout, Webhook, Usage, Admin plan management.

Endpoints:
  POST /billing/checkout          — create Stripe Checkout Session
  POST /billing/webhook           — Stripe webhook (updates plan in DB)
  GET  /billing/usage             — current usage counters for UI
  PATCH /billing/admin/users/{id}/plan — manual plan override (admin only)
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.db import get_db
from app.models import User, UserUsage
from app.services.billing import (
    PLAN_LIMITS,
    _current_period,
    _effective_plan,
    get_limits,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

# ─── Stripe price → (plan, mode, extra) map ──────────────────────────────────
# mode: "subscription" | "payment"
# extra: optional dict with special actions (e.g. live_sessions delta)
def _price_plan_map() -> dict:
    return {
        settings.STRIPE_PRICE_PLUS_MONTHLY:   ("plus",         "subscription", {}),
        settings.STRIPE_PRICE_PLUS_ANNUAL:    ("plus",         "subscription", {}),
        settings.STRIPE_PRICE_PRO_MONTHLY:    ("pro",          "subscription", {}),
        settings.STRIPE_PRICE_PRO_ANNUAL:     ("pro",          "subscription", {}),
        settings.STRIPE_PRICE_LIFETIME:       ("lifetime",     "payment",      {}),
        settings.STRIPE_PRICE_LIFETIME_PRO:   ("lifetime_pro", "payment",      {"live_sessions_add": 100}),
        settings.STRIPE_PRICE_EXTRA_MEMORIAL: (None,           "payment",      {"extra_memorials_add": 1}),
        settings.STRIPE_PRICE_LIVE_SESSION_PACK: (None,        "payment",      {"live_sessions_add": 10}),
    }


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str                          # "plus_monthly" | "plus_annual" | "pro_monthly" | "pro_annual" | "lifetime" | "lifetime_pro" | "extra_memorial" | "live_session_pack"
    memorial_id: Optional[int] = None  # required for lifetime / lifetime_pro
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class UsageResponse(BaseModel):
    plan: str
    period: str
    chat_messages_used: int
    chat_messages_limit: int
    animations_used: int
    animations_limit: int
    live_sessions_used: int
    live_sessions_limit: Optional[int]   # None = pool model
    live_sessions_remaining: Optional[int]  # pool (lifetime_pro)
    extra_memorials: int
    plan_expires_at: Optional[datetime]


_PLAN_KEY_TO_PRICE = {
    "plus_monthly":       lambda: settings.STRIPE_PRICE_PLUS_MONTHLY,
    "plus_annual":        lambda: settings.STRIPE_PRICE_PLUS_ANNUAL,
    "pro_monthly":        lambda: settings.STRIPE_PRICE_PRO_MONTHLY,
    "pro_annual":         lambda: settings.STRIPE_PRICE_PRO_ANNUAL,
    "lifetime":           lambda: settings.STRIPE_PRICE_LIFETIME,
    "lifetime_pro":       lambda: settings.STRIPE_PRICE_LIFETIME_PRO,
    "extra_memorial":     lambda: settings.STRIPE_PRICE_EXTRA_MEMORIAL,
    "live_session_pack":  lambda: settings.STRIPE_PRICE_LIVE_SESSION_PACK,
}

_SUBSCRIPTION_PLANS = {"plus_monthly", "plus_annual", "pro_monthly", "pro_annual"}
_LIFETIME_PLANS = {"lifetime", "lifetime_pro"}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/checkout")
async def create_checkout(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe Checkout Session and return the redirect URL.
    The client should redirect the user to session.url.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured. Set STRIPE_SECRET_KEY in backend/.env.",
        )

    price_getter = _PLAN_KEY_TO_PRICE.get(body.plan)
    if not price_getter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown plan key '{body.plan}'. Valid: {list(_PLAN_KEY_TO_PRICE)}",
        )
    price_id = price_getter()
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Stripe price for '{body.plan}' is not configured. Set the corresponding STRIPE_PRICE_* env var.",
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    is_subscription = body.plan in _SUBSCRIPTION_PLANS
    mode = "subscription" if is_subscription else "payment"

    success_url = body.success_url or f"{settings.PUBLIC_FRONTEND_URL}/app?checkout=success&plan={body.plan}"
    cancel_url  = body.cancel_url  or f"{settings.PUBLIC_FRONTEND_URL}/app/pricing?checkout=cancel"

    # Pass user_id + memorial_id in metadata so webhook can update DB
    metadata = {
        "user_id":    str(current_user.id),
        "plan_key":   body.plan,
        "memorial_id": str(body.memorial_id) if body.memorial_id else "",
    }

    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            customer_email=current_user.email,
            metadata=metadata,
            # Pass metadata to subscription so it's available on invoice events
            **({"subscription_data": {"metadata": metadata}} if is_subscription else {}),
        )
    except stripe.StripeError as e:
        logger.error("Stripe checkout error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {e.user_message or str(e)}",
        )

    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """
    Stripe webhook handler. Verifies signature and updates user plan in DB.
    Register this URL in Stripe Dashboard → Webhooks.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe signature")

    logger.info("Stripe webhook: %s", event["type"])

    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"], db)
    elif event["type"] in ("invoice.payment_succeeded", "invoice.paid"):
        _handle_invoice_paid(event["data"]["object"], db)
    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        _handle_subscription_cancelled(event["data"]["object"], db)

    return {"ok": True}


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns current billing period usage counters for the UI."""
    plan = _effective_plan(current_user)
    limits = get_limits(current_user)
    period = _current_period()

    usage = (
        db.query(UserUsage)
        .filter(UserUsage.user_id == current_user.id, UserUsage.period == period)
        .first()
    )
    chat_used = usage.chat_messages if usage else 0
    anim_used = usage.animations if usage else 0
    live_used = usage.live_sessions if usage else 0

    uses_pool = limits.get("live_session_pool", False)

    return UsageResponse(
        plan=plan,
        period=period,
        chat_messages_used=chat_used,
        chat_messages_limit=limits["chat_messages_per_month"],
        animations_used=anim_used,
        animations_limit=limits["animations_per_month"],
        live_sessions_used=live_used,
        live_sessions_limit=None if uses_pool else limits.get("live_sessions_per_month", 0),
        live_sessions_remaining=current_user.live_sessions_remaining if uses_pool else None,
        extra_memorials=current_user.extra_memorials or 0,
        plan_expires_at=current_user.plan_expires_at,
    )


# ─── Admin endpoint ───────────────────────────────────────────────────────────

class AdminPlanUpdate(BaseModel):
    plan: str                              # free|plus|pro|lifetime|lifetime_pro
    expires_days: Optional[int] = None    # for plus/pro; None = no expiry change
    memorial_id: Optional[int] = None     # required for lifetime plans
    live_sessions: Optional[int] = None   # set absolute pool for lifetime_pro


@router.patch("/admin/users/{user_id}/plan")
def admin_update_plan(
    user_id: int,
    body: AdminPlanUpdate,
    db: Session = Depends(get_db),
    x_admin_key: Optional[str] = Header(None, alias="x-admin-key"),
):
    """
    Manually override a user's subscription plan.
    Requires X-Admin-Key header matching ADMIN_SECRET_KEY or SECRET_KEY.
    """
    valid_key = settings.ADMIN_SECRET_KEY or settings.SECRET_KEY
    if x_admin_key != valid_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")

    if body.plan not in PLAN_LIMITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown plan '{body.plan}'. Valid: {list(PLAN_LIMITS)}",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.subscription_plan = body.plan

    if body.expires_days is not None and body.plan in ("plus", "pro"):
        user.plan_expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_days)
    elif body.plan in ("lifetime", "lifetime_pro", "free"):
        user.plan_expires_at = None

    if body.memorial_id and body.plan in ("lifetime", "lifetime_pro"):
        user.lifetime_memorial_id = body.memorial_id

    if body.live_sessions is not None and body.plan == "lifetime_pro":
        user.live_sessions_remaining = body.live_sessions
    elif body.plan == "lifetime_pro" and user.live_sessions_remaining == 0:
        user.live_sessions_remaining = 100  # default pool on first assignment

    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "user_id": user.id,
        "plan": user.subscription_plan,
        "plan_expires_at": user.plan_expires_at,
        "lifetime_memorial_id": user.lifetime_memorial_id,
        "live_sessions_remaining": user.live_sessions_remaining,
        "extra_memorials": user.extra_memorials,
    }


# ─── Webhook helpers ──────────────────────────────────────────────────────────

def _handle_checkout_completed(session: dict, db: Session) -> None:
    meta = session.get("metadata") or {}
    user_id   = _int(meta.get("user_id"))
    plan_key  = meta.get("plan_key", "")
    memorial_id = _int(meta.get("memorial_id"))

    if not user_id:
        logger.warning("checkout.session.completed missing user_id in metadata")
        return

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning("checkout.session.completed: user %s not found", user_id)
        return

    price_map = _price_plan_map()
    # Find the price_id from session line_items (simple: use plan_key mapping)
    price_getter = _PLAN_KEY_TO_PRICE.get(plan_key)
    if not price_getter:
        logger.warning("Unknown plan_key in metadata: %s", plan_key)
        return
    price_id = price_getter()
    entry = price_map.get(price_id)
    if not entry:
        logger.warning("Price %s not in price_plan_map", price_id)
        return

    new_plan, mode, extra = entry

    if new_plan:
        user.subscription_plan = new_plan

    # Subscription: expiry set by invoice.payment_succeeded; here just record plan
    if mode == "payment":
        # One-time purchases
        if new_plan in ("lifetime", "lifetime_pro"):
            user.plan_expires_at = None
            if memorial_id:
                user.lifetime_memorial_id = memorial_id
        if new_plan == "lifetime_pro" and user.live_sessions_remaining == 0:
            user.live_sessions_remaining = extra.get("live_sessions_add", 100)
        elif extra.get("live_sessions_add") and new_plan is None:
            # Add-on pack
            user.live_sessions_remaining = (user.live_sessions_remaining or 0) + extra["live_sessions_add"]
        if extra.get("extra_memorials_add"):
            user.extra_memorials = (user.extra_memorials or 0) + extra["extra_memorials_add"]

    db.commit()
    logger.info("Plan updated: user=%s plan=%s via checkout", user_id, user.subscription_plan)


def _handle_invoice_paid(invoice: dict, db: Session) -> None:
    """Subscription renewal: extend plan_expires_at by ~1 month or ~1 year."""
    sub_id = invoice.get("subscription")
    if not sub_id:
        return

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        sub = stripe.Subscription.retrieve(sub_id)
    except Exception as e:
        logger.error("Could not retrieve subscription %s: %s", sub_id, e)
        return

    meta = sub.get("metadata") or {}
    user_id  = _int(meta.get("user_id"))
    plan_key = meta.get("plan_key", "")
    if not user_id:
        return

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    # Determine billing period from subscription
    current_period_end = sub.get("current_period_end")
    if current_period_end:
        user.plan_expires_at = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

    if plan_key.startswith("plus"):
        user.subscription_plan = "plus"
    elif plan_key.startswith("pro"):
        user.subscription_plan = "pro"

    db.commit()
    logger.info("Subscription renewed: user=%s expires=%s", user_id, user.plan_expires_at)


def _handle_subscription_cancelled(subscription: dict, db: Session) -> None:
    meta = subscription.get("metadata") or {}
    user_id = _int(meta.get("user_id"))
    if not user_id:
        return

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    user.subscription_plan = "free"
    user.plan_expires_at = None
    db.commit()
    logger.info("Subscription cancelled: user=%s → free", user_id)


def _int(v) -> Optional[int]:
    try:
        return int(v) if v else None
    except (TypeError, ValueError):
        return None
