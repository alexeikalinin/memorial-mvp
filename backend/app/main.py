"""
Главный файл FastAPI приложения.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import engine, Base
from app.api import health, memorials, ai, media, s3, embeddings, family, invites, access as access_router
from app.api import auth as auth_router

# Создание таблиц в БД (для dev; в production используйте Alembic миграции)
Base.metadata.create_all(bind=engine)

# Миграция: создаём MemorialAccess(OWNER) для мемориалов, у которых ещё нет записи
from app.db import SessionLocal
from app.models import Memorial, MemorialAccess, User, UserRole
from app.auth import hash_password

def _add_missing_columns():
    """Добавляет новые колонки в существующие таблицы (SQLite не поддерживает ALTER через create_all)."""
    with engine.connect() as conn:
        from sqlalchemy import text
        migrations = [
            "ALTER TABLE memorials ADD COLUMN language VARCHAR(5) NOT NULL DEFAULT 'ru'",
            "ALTER TABLE users ADD COLUMN google_id VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)",
        ]
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # Колонка уже существует — игнорируем
_add_missing_columns()

def _ensure_default_user():
    """Создаёт дефолтного пользователя id=1 для dev-режима (DEBUG=True)."""
    if not settings.DEBUG:
        return
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.id == 1).first():
            user = User(
                id=1,
                email="dev@memorial.app",
                username="dev",
                hashed_password=hash_password("devpassword"),
                is_active=True,
            )
            db.add(user)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
_ensure_default_user()

def _migrate_existing_access():
    db = SessionLocal()
    try:
        from sqlalchemy import select as sa_select
        existing_owner_ids = sa_select(MemorialAccess.memorial_id).where(
            MemorialAccess.role == UserRole.OWNER
        )
        memorials_without_access = (
            db.query(Memorial)
            .filter(Memorial.id.notin_(existing_owner_ids))
            .all()
        )
        for m in memorials_without_access:
            access = MemorialAccess(memorial_id=m.id, user_id=m.owner_id, role=UserRole.OWNER)
            db.add(access)
        if memorials_without_access:
            db.commit()
            print(f"Migrated {len(memorials_without_access)} memorials to MemorialAccess table")
    except Exception as e:
        db.rollback()
        print(f"Warning: access migration failed: {e}")
    finally:
        db.close()
_migrate_existing_access()

# Создание FastAPI приложения
app = FastAPI(
    title="Memorial MVP API",
    description="API для веб-сервиса хранения цифровой памяти и создания ИИ-аватаров",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(memorials.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(media.router, prefix=settings.API_V1_PREFIX)
app.include_router(s3.router, prefix=settings.API_V1_PREFIX)
app.include_router(embeddings.router, prefix=settings.API_V1_PREFIX)
app.include_router(family.router, prefix=settings.API_V1_PREFIX)
app.include_router(invites.router, prefix=settings.API_V1_PREFIX)
app.include_router(access_router.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "message": "Memorial MVP API",
        "version": "0.1.0",
        "docs": "/docs"
    }

