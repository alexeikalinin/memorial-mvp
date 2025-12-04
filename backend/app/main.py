"""
Главный файл FastAPI приложения.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import engine, Base
from app.api import health, memorials, ai, media, s3, embeddings, family

# Создание таблиц в БД (для dev; в production используйте Alembic миграции)
Base.metadata.create_all(bind=engine)

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
app.include_router(memorials.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(media.router, prefix=settings.API_V1_PREFIX)
app.include_router(s3.router, prefix=settings.API_V1_PREFIX)
app.include_router(embeddings.router, prefix=settings.API_V1_PREFIX)
app.include_router(family.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "message": "Memorial MVP API",
        "version": "0.1.0",
        "docs": "/docs"
    }

