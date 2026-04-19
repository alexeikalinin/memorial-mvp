"""
Главный файл FastAPI приложения.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import engine, Base
from app.api import health, memorials, ai, media, s3, embeddings, family, invites, access as access_router, waitlist, billing as billing_router
from app.api import auth as auth_router

# Создание таблиц в БД (для dev; в production используйте Alembic миграции)
Base.metadata.create_all(bind=engine)

# Миграция: создаём MemorialAccess(OWNER) для мемориалов, у которых ещё нет записи
from app.db import SessionLocal
from app.models import Memorial, MemorialAccess, User, UserRole
from app.auth import hash_password

def _add_missing_columns():
    """Добавляет новые колонки в существующие таблицы (create_all не обновляет старые таблицы)."""
    from sqlalchemy import text, inspect

    insp = inspect(engine)
    if insp.has_table("memorials"):
        cols = {c["name"] for c in insp.get_columns("memorials")}
        if "language" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE memorials ADD COLUMN language VARCHAR(5) NOT NULL DEFAULT 'ru'"
                    )
                )
        if "tree_layout_json" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE memorials ADD COLUMN tree_layout_json JSON"))
    if insp.has_table("users"):
        ucols = {c["name"] for c in insp.get_columns("users")}
        user_alters = []
        if "google_id" not in ucols:
            user_alters.append("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)")
        if "avatar_url" not in ucols:
            user_alters.append("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)")
        if "subscription_plan" not in ucols:
            user_alters.append("ALTER TABLE users ADD COLUMN subscription_plan VARCHAR(20) NOT NULL DEFAULT 'free'")
        if "plan_expires_at" not in ucols:
            user_alters.append("ALTER TABLE users ADD COLUMN plan_expires_at TIMESTAMP WITH TIME ZONE")
        if "lifetime_memorial_id" not in ucols:
            user_alters.append("ALTER TABLE users ADD COLUMN lifetime_memorial_id INTEGER")
        if user_alters:
            with engine.begin() as conn:
                for sql in user_alters:
                    conn.execute(text(sql))


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


def _warn_qdrant_if_deployed_without_cloud():
    """Локальный Qdrant по умолчанию недоступен из облачного контейнера (Railway и т.д.)."""
    if settings.VECTOR_DB_PROVIDER != "qdrant":
        return
    if settings.QDRANT_LOCAL_PATH:
        return
    url = (settings.QDRANT_URL or "").lower()
    if "localhost" not in url and "127.0.0.1" not in url:
        return
    if not (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("DYNO")):
        return
    print(
        "WARNING: QDRANT_URL points to localhost but QDRANT_LOCAL_PATH is empty. "
        "Avatar chat (RAG) will fail until you set QDRANT_URL + QDRANT_API_KEY (Qdrant Cloud) "
        "or a persistent QDRANT_LOCAL_PATH. See backend/.env.example."
    )


_warn_qdrant_if_deployed_without_cloud()

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
app.include_router(waitlist.router, prefix=settings.API_V1_PREFIX)
app.include_router(billing_router.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def _auto_rebuild_embeddings_if_empty():
    """При старте: если Qdrant-коллекция пустая — перестраиваем embeddings в фоне."""
    import asyncio
    from app.services.ai_tasks import get_vector_db_client, get_embedding, upsert_memory_embedding

    if not settings.OPENAI_API_KEY:
        return

    async def _rebuild():
        try:
            client = get_vector_db_client()
            info = client.get_collection(settings.QDRANT_COLLECTION_NAME)
            if info.points_count > 0:
                print(f"Qdrant: {info.points_count} vectors already present, skipping auto-rebuild.")
                return
        except Exception:
            pass  # коллекция не существует — создастся при первом upsert

        print("Qdrant: collection empty, starting background embedding rebuild...")
        db = SessionLocal()
        try:
            from app.models import Memory
            memories = db.query(Memory).all()
            ok = 0
            for memory in memories:
                try:
                    embedding = await get_embedding(memory.content)
                    eid = await upsert_memory_embedding(
                        memory_id=memory.id,
                        memorial_id=memory.memorial_id,
                        embedding=embedding,
                        text=memory.content,
                    )
                    if eid:
                        memory.embedding_id = eid
                        ok += 1
                except Exception as e:
                    print(f"  embedding error memory_id={memory.id}: {e}")
            db.commit()
            print(f"Qdrant auto-rebuild done: {ok}/{len(memories)} embeddings created.")
        except Exception as e:
            print(f"Qdrant auto-rebuild failed: {e}")
        finally:
            db.close()

    asyncio.create_task(_rebuild())


@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "message": "Memorial MVP API",
        "version": "0.1.0",
        "docs": "/docs"
    }

