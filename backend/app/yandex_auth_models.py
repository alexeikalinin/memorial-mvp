"""Yandex identities and short-lived, single-use browser login transactions."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from app.db import Base


class YandexIdentity(Base):
    __tablename__ = 'yandex_identities'
    subject = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)


class YandexAttempt(Base):
    __tablename__ = 'yandex_attempts'
    state_hash = Column(String(64), primary_key=True)
    browser_hash = Column(String(64), nullable=False)
    provider_verifier = Column(String(128), nullable=False)
    frontend_challenge = Column(String(43), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


class YandexTicket(Base):
    __tablename__ = 'yandex_tickets'
    ticket_hash = Column(String(64), primary_key=True)
    frontend_challenge = Column(String(43), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_new = Column(Boolean, nullable=False, default=False)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


def protect_yandex_tables(engine):
    """Keep OAuth transaction metadata out of Supabase's public data API."""
    if engine.dialect.name != 'postgresql':
        return
    from sqlalchemy import text
    with engine.begin() as conn:
        for table in ('yandex_identities', 'yandex_attempts', 'yandex_tickets'):
            conn.execute(text(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY'))
