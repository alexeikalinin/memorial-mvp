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
    voice_gender: Optional[str] = None  # "male" | "female" — пол для выбора голоса озвучки


class MemorialCreate(MemorialBase):
    pass


class MemorialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    is_public: Optional[bool] = None
    voice_id: Optional[str] = None
    voice_gender: Optional[str] = None
    cover_photo_id: Optional[int] = None


class MemorialResponse(MemorialBase):
    id: int
    owner_id: int
    voice_id: Optional[str] = None
    voice_gender: Optional[str] = None
    cover_photo_id: Optional[int] = None
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
    event_date: Optional[datetime] = None  # Дата события (когда это было)


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    event_date: Optional[datetime] = None


class MemoryResponse(MemoryBase):
    id: int
    memorial_id: int
    embedding_id: Optional[str] = None
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


class MemorialListItem(BaseModel):
    """Краткая информация о мемориале для списка."""
    id: int
    name: str
    description: Optional[str] = None
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    is_public: bool
    cover_photo_id: Optional[int] = None
    memories_count: int = 0
    media_count: int = 0
    created_at: datetime


class SetCoverRequest(BaseModel):
    media_id: Optional[int] = None  # None чтобы снять обложку


class TimelineItem(BaseModel):
    id: int
    year: int
    date_label: str
    type: str
    title: Optional[str] = None
    content: str
    event_date: datetime

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
    task_id: str  # Может быть Celery task ID или HeyGen video_id
    media_id: Optional[int] = None  # Если указан, используется для поиска video_id в БД
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
    use_persona: bool = True  # Использовать Smart Avatar Persona Agent для системного промпта
    include_family_memories: bool = False  # Включить воспоминания родственников в RAG-поиск


class AvatarChatResponse(BaseModel):
    answer: str
    audio_url: Optional[str] = None
    audio_error: Optional[str] = None  # Причина сбоя генерации аудио (если include_audio=True, но аудио нет)
    animation_task_id: Optional[str] = None
    animation_provider: Optional[str] = None  # "d-id" или "heygen"
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
    cover_photo_id: Optional[int] = None  # ID фото обложки для построения URL на фронтенде
    children: List["FamilyTreeNode"] = []
    spouses: List["FamilyTreeNode"] = []
    
    class Config:
        from_attributes = True


class FamilyTreeResponse(BaseModel):
    """Семейное дерево мемориала."""
    root: FamilyTreeNode
    total_nodes: int


# Invite Schemas
class InviteCreate(BaseModel):
    label: Optional[str] = None
    expires_days: Optional[int] = None  # None = бессрочный


class InviteResponse(BaseModel):
    token: str
    label: Optional[str] = None
    invite_url: str
    expires_at: Optional[datetime] = None
    uses_count: int
    permissions: Dict

    class Config:
        from_attributes = True


class InviteValidateResponse(BaseModel):
    memorial_id: int
    memorial_name: str
    cover_photo_id: Optional[int] = None
    label: Optional[str] = None
    permissions: Dict

