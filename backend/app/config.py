"""
Конфигурация приложения через переменные окружения.
"""
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List

# .env всегда ищем в корне backend (независимо от cwd при запуске uvicorn)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./memorial.db"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 дней
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    @field_validator("OPENAI_MODEL", mode="before")
    @classmethod
    def normalize_openai_model(cls, v):
        """Имена вроде gpt-4-turbo-preview сняты с API → 404; подменяем на рабочий дефолт."""
        if not isinstance(v, str):
            return "gpt-4o-mini"
        s = v.strip()
        deprecated = frozenset(
            {
                "gpt-4-turbo-preview",  # типичная 404 в проде при старом .env
                "gpt-4-0125-preview",
                "gpt-4-1106-preview",
            }
        )
        if s in deprecated:
            return "gpt-4o-mini"
        return s
    
    # D-ID
    DID_API_KEY: str = ""
    DID_API_URL: str = "https://api.d-id.com"
    DID_WEBHOOK_URL: str = ""  # URL для webhook'ов от D-ID
    
    # HeyGen (альтернатива D-ID)
    HEYGEN_API_KEY: str = ""
    HEYGEN_API_URL: str = "https://api.heygen.com/v2"
    USE_HEYGEN: bool = False  # Использовать HeyGen вместо D-ID
    HEYGEN_TALKING_PHOTO_ID: str = ""  # ID talking_photo, созданного через веб-интерфейс (опционально)
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""  # Голос по умолчанию (если не задан пол)

    @field_validator("ELEVENLABS_API_KEY", mode="before")
    @classmethod
    def strip_elevenlabs_key(cls, v):
        """Убирает пробелы и перевод строк из ключа (частая причина 401 при копировании из .env)."""
        if isinstance(v, str):
            return v.strip()
        return v
    ELEVENLABS_VOICE_ID_MALE: str = ""   # Мужской голос для мемориалов с voice_gender=male
    ELEVENLABS_VOICE_ID_FEMALE: str = "" # Женский голос для мемориалов с voice_gender=female
    
    # Vector Database - выбор между Pinecone и Qdrant
    VECTOR_DB_PROVIDER: str = "qdrant"  # "pinecone" или "qdrant"
    
    # Pinecone (если VECTOR_DB_PROVIDER="pinecone")
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "memorial-memories"
    
    # Qdrant (если VECTOR_DB_PROVIDER="qdrant")
    QDRANT_URL: str = "http://localhost:6333"  # Локальный или Qdrant Cloud URL
    QDRANT_API_KEY: str = ""  # Опционально, для Qdrant Cloud
    QDRANT_COLLECTION_NAME: str = "memorial-memories"
    QDRANT_LOCAL_PATH: str = ""  # Пустая строка = использовать QDRANT_URL (cloud). Задай путь для локальной разработки.
    
    # Supabase
    SUPABASE_URL: str = ""  # https://xxxx.supabase.co

    # S3-совместимое хранилище (Supabase Storage или AWS S3)
    S3_BUCKET_NAME: str = "memorial-media"
    S3_REGION: str = "eu-central-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    USE_S3: bool = False

    @property
    def s3_endpoint_url(self) -> str:
        """S3 endpoint: Supabase Storage если SUPABASE_URL задан, иначе AWS."""
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL}/storage/v1/s3"
        return ""

    @property
    def supabase_public_url(self) -> str:
        """Базовый URL для публичных файлов в Supabase Storage."""
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL}/storage/v1/object/public/{self.S3_BUCKET_NAME}"
        return ""
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""  # Имя бота без @, для deep links
    BOT_API_BASE_URL: str = "http://localhost:8000/api/v1"
    
    # Global admins (comma-separated emails): full owner-level API access to every memorial
    # without a row in memorial_access. Use for prod operators; pair with grant_owner script for DB consistency.
    GLOBAL_ADMIN_EMAILS: str = ""

    # Application
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    # Локальная разработка + прод фронт на Vercel (можно дописать через env CORS_ORIGINS)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://memorial-mvp.vercel.app"
    PUBLIC_API_URL: str = ""  # Публичный URL для доступа к API (для HeyGen и других внешних сервисов)
    PUBLIC_FRONTEND_URL: str = "http://localhost:5173"  # Публичный URL фронтенда (для QR-кодов)
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif,mp4,mov,mp3,wav,pdf,txt"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Преобразует строку CORS_ORIGINS в список."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Преобразует строку ALLOWED_EXTENSIONS в список."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    class Config:
        env_file = str(_ENV_FILE)
        case_sensitive = True


# Глобальный экземпляр настроек
settings = Settings()

