"""Single-use Google web OAuth transactions, separate from mobile and Yandex."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from app.db import Base


class GoogleWebAttempt(Base):
    __tablename__ = 'google_web_attempts'
    state_hash = Column(String(64), primary_key=True)
    browser_hash = Column(String(64), nullable=False)
    provider_verifier = Column(String(128), nullable=False)
    frontend_challenge = Column(String(43), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


class GoogleWebTicket(Base):
    __tablename__ = 'google_web_tickets'
    ticket_hash = Column(String(64), primary_key=True)
    frontend_challenge = Column(String(43), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_new = Column(Boolean, nullable=False, default=False)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)



def protect_google_web_tables(engine):
    if engine.dialect.name != 'postgresql':
        return
    from sqlalchemy import text
    with engine.begin() as conn:
        for table in ('google_web_attempts', 'google_web_tickets'):
            conn.execute(text(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY'))
        conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id_unique ON users (google_id)'))
