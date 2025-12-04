"""
Конфигурация приложения через переменные окружения.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./memorial.db"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # D-ID
    DID_API_KEY: str = ""
    DID_API_URL: str = "https://api.d-id.com"
    DID_WEBHOOK_URL: str = ""  # URL для webhook'ов от D-ID
    
    # HeyGen (альтернатива D-ID)
    HEYGEN_API_KEY: str = ""
    HEYGEN_API_URL: str = "https://api.heygen.com/v2"
    USE_HEYGEN: bool = False  # Использовать HeyGen вместо D-ID
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""
    
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
    
    # AWS S3
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    USE_S3: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Application
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    PUBLIC_API_URL: str = ""  # Публичный URL для доступа к API (для HeyGen и других внешних сервисов)
    
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
        env_file = ".env"
        case_sensitive = True


# Глобальный экземпляр настроек
settings = Settings()

