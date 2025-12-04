"""
Pydantic схемы для валидации и сериализации данных.
"""
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.models import MediaType, RelationshipType


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Memorial Schemas
class MemorialBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    is_public: bool = False


class MemorialCreate(MemorialBase):
    pass


class MemorialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    is_public: Optional[bool] = None
    voice_id: Optional[str] = None


class MemorialResponse(MemorialBase):
    id: int
    owner_id: int
    voice_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Media Schemas
class MediaBase(BaseModel):
    file_name: str
    media_type: MediaType


class MediaCreate(BaseModel):
    file_name: str
    media_type: MediaType


class MediaResponse(MediaBase):
    id: int
    memorial_id: int
    file_path: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    thumbnail_path: Optional[str] = None
    is_animated: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


# Memory Schemas
class MemoryBase(BaseModel):
    title: Optional[str] = None
    content: str = Field(..., min_length=1)


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)


class MemoryResponse(MemoryBase):
    id: int
    memorial_id: int
    embedding_id: Optional[str] = None  # Добавляем embedding_id в ответ
    source: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MemorialDetailResponse(MemorialResponse):
    """Мемориал с медиа и воспоминаниями."""
    media: List[MediaResponse] = []
    memories: List[MemoryResponse] = []
    
    class Config:
        from_attributes = True


# AI Schemas
class PhotoAnimateRequest(BaseModel):
    media_id: int
    prompt: Optional[str] = None  # Опциональный промпт для анимации


class PhotoAnimateResponse(BaseModel):
    task_id: str
    status: str
    message: str
    provider: Optional[str] = None  # "d-id" или "heygen"


class AnimationStatusRequest(BaseModel):
    task_id: str
    provider: Optional[str] = None  # Если не указан, определяется автоматически


class AnimationStatusResponse(BaseModel):
    task_id: str
    status: str  # "processing", "done", "error"
    video_url: Optional[str] = None
    error: Optional[str] = None
    provider: str


class AvatarChatRequest(BaseModel):
    memorial_id: int
    question: str = Field(..., min_length=1)
    include_audio: bool = False  # Генерировать ли аудио-ответ через ElevenLabs


class AvatarChatResponse(BaseModel):
    answer: str
    audio_url: Optional[str] = None
    sources: List[str] = []  # Список использованных фрагментов воспоминаний


# S3 Schemas
class PresignedUploadUrlRequest(BaseModel):
    file_name: str
    content_type: str
    file_size: int


class PresignedUploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int


# Family Tree Schemas
class FamilyRelationshipCreate(BaseModel):
    related_memorial_id: int
    relationship_type: RelationshipType
    notes: Optional[str] = None


class FamilyRelationshipResponse(BaseModel):
    id: int
    memorial_id: int
    related_memorial_id: int
    relationship_type: RelationshipType
    notes: Optional[str] = None
    related_memorial_name: Optional[str] = None  # Имя связанного мемориала
    created_at: datetime
    
    class Config:
        from_attributes = True


class FamilyTreeNode(BaseModel):
    """Узел семейного дерева."""
    memorial_id: int
    name: str
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    relationship_type: Optional[RelationshipType] = None  # Тип связи с родительским узлом
    children: List["FamilyTreeNode"] = []
    spouses: List["FamilyTreeNode"] = []
    
    class Config:
        from_attributes = True


class FamilyTreeResponse(BaseModel):
    """Семейное дерево мемориала."""
    root: FamilyTreeNode
    total_nodes: int

