"""Short-lived mobile OAuth attempts; no Google tokens or device verifiers are stored."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.db import Base


class MobileGoogleAttempt(Base):
    __tablename__ = 'mobile_google_attempts'
    id = Column(String(64), primary_key=True)
    challenge = Column(String(43), nullable=False)
    code_hash = Column(String(64), nullable=True)
    status = Column(String(16), nullable=False, default='pending')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)

