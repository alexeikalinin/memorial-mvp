"""
Публичный сбор email для уведомлений о запуске оплаты / полного функционала.
"""
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.db import get_db
from app.models import WaitlistSignup
from app.schemas import WaitlistSignupCreate, WaitlistSignupResponse

router = APIRouter()


@router.post("/waitlist/", response_model=WaitlistSignupResponse)
def create_waitlist_signup(body: WaitlistSignupCreate, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    existing = db.query(WaitlistSignup).filter(WaitlistSignup.email == email).first()
    if existing:
        return WaitlistSignupResponse(
            ok=True,
            message="You're already on the list. We'll email you when paid features and checkout go live.",
            already_registered=True,
        )
    row = WaitlistSignup(email=email, source=(body.source or "landing")[:64])
    db.add(row)
    db.commit()
    return WaitlistSignupResponse(
        ok=True,
        message="Thank you. We'll email you when the service is fully available — including voice, animation, and checkout.",
        already_registered=False,
    )
