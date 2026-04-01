"""
Настройка базы данных и сессий SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

_is_sqlite = "sqlite" in settings.DATABASE_URL
_is_postgres = "postgresql" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL

# Настройки движка в зависимости от БД
if _is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.SQL_ECHO,
    )
elif _is_postgres:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,   # проверяем соединение перед использованием
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,     # переиспользуем соединения каждые 5 мин (для pgBouncer)
        echo=settings.SQL_ECHO,
    )
else:
    engine = create_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db():
    """
    Dependency для получения сессии базы данных.
    Используется в FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

