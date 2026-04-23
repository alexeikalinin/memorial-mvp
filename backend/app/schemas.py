"""
Pydantic схемы для валидации и сериализации данных.
"""
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import MediaType, RelationshipType


# Access Management Schemas
class AccessEntryResponse(BaseModel):
    id: int
    memorial_id: int
    user_id: int
    user_email: str
    user_username: str
    user_full_name: Optional[str] = None
    role: str  # "owner" | "editor" | "viewer"
    granted_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GrantAccessRequest(BaseModel):
    email: EmailStr
    role: str = "viewer"  # "editor" | "viewer" (нельзя дать owner через этот endpoint)


class UpdateAccessRequest(BaseModel):
    role: str  # "editor" | "viewer"


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
    is_demo: bool = False
    subscription_plan: str = "free"
    created_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas (после UserResponse, т.к. TokenWithUser ссылается на него)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Memorial Schemas
class MemorialBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    is_public: bool = False
    voice_gender: Optional[str] = None  # "male" | "female" — пол для выбора голоса озвучки
    language: str = "ru"  # "ru" | "en"


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
    tree_layout_json: Optional[Dict[str, Any]] = None


class MemorialResponse(MemorialBase):
    id: int
    owner_id: int
    voice_id: Optional[str] = None
    voice_gender: Optional[str] = None
    cover_photo_id: Optional[int] = None
    tree_layout_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_demo: bool = False

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
    current_user_role: Optional[str] = None  # "owner" | "editor" | "viewer" | null

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
    cover_photo_url: Optional[str] = None
    memories_count: int = 0
    media_count: int = 0
    language: str = "ru"
    created_at: datetime
    is_demo_seed: bool = False  # EN демо из en_memorials_manifest (скрыть на главной по умолчанию)


class SetCoverRequest(BaseModel):
    media_id: Optional[int] = None  # None чтобы снять обложку


class TimelineItem(BaseModel):
    id: int
    year: int
    date_label: str
    type: str
    title: Optional[str] = None
    content: str
    event_date: Optional[datetime] = None  # None = воспоминание без даты события (секция «без даты»)

    class Config:
        from_attributes = True


# ElevenLabs (квота для UI)
class ElevenLabsQuotaResponse(BaseModel):
    configured: bool = True
    tier: Optional[str] = None
    character_count: int = 0
    character_limit: int = 0
    characters_remaining: int = 0
    next_character_count_reset_unix: Optional[int] = None


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
    language: str = "ru"  # "ru" | "en" — язык ответа аватара


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
    custom_label: Optional[str] = Field(None, max_length=100)  # обязательно для CUSTOM типа
    notes: Optional[str] = None


class FamilyRelationshipResponse(BaseModel):
    id: int
    memorial_id: int
    related_memorial_id: int
    relationship_type: RelationshipType
    custom_label: Optional[str] = None
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


# Скрытые родственные связи
class ConnectionStep(BaseModel):
    """Один шаг в цепочке родства."""
    memorial_id: int
    name: str
    relationship_label: str  # «мать», «супруг», «ребёнок», «брат/сестра»


class HiddenConnection(BaseModel):
    """Неочевидная родственная связь через несколько поколений."""
    target_memorial_id: int
    target_name: str
    path: List[ConnectionStep]   # цепочка от текущего до target
    hops: int                    # длина цепочки (1 = прямая связь, 2+ = скрытая)
    connection_summary: str      # «Троюродный брат через Людмилу Ковалёву и Николая Морозова»


class HiddenConnectionsResponse(BaseModel):
    hidden: List[HiddenConnection]   # hops >= 2
    direct: List[HiddenConnection]   # hops == 1 (прямые, для справки)


# Full bidirectional graph (ancestors + descendants + cross-family connections)
class FullTreeNode(BaseModel):
    memorial_id: int
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    cover_photo_id: Optional[int] = None
    voice_gender: Optional[str] = None  # для UI (рамка «жена» между семьями)
    generation: int   # 0=root, negative=ancestors, positive=descendants


class FullTreeEdge(BaseModel):
    source: int
    target: int
    type: str  # parent, child, spouse, sibling, custom
    label: Optional[str] = None  # custom_label for custom edges


class FullFamilyTreeResponse(BaseModel):
    nodes: List[FullTreeNode]
    edges: List[FullTreeEdge]
    root_id: int


# Network Clusters (cross-family visualization)
class NetworkClusterMember(BaseModel):
    memorial_id: int
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    cover_photo_id: Optional[int] = None
    is_alive: bool = False


class NetworkCluster(BaseModel):
    cluster_id: int
    label: str           # e.g. "Kelly · Anderson" (surnames found in cluster)
    members: List[NetworkClusterMember]
    color: str           # hex color for this cluster island


class NetworkBridge(BaseModel):
    source_cluster_id: int
    target_cluster_id: int
    source_memorial_id: int
    target_memorial_id: int
    source_name: str
    target_name: str
    label: str           # custom_label from DB


class NetworkClustersResponse(BaseModel):
    clusters: List[NetworkCluster]
    bridges: List[NetworkBridge]
    focal_cluster_id: int   # which cluster the requested memorial belongs to


# Access Request Schemas
class AccessRequestCreate(BaseModel):
    requested_role: str = "viewer"  # "editor" | "viewer"
    message: Optional[str] = None


class AccessRequestResponse(BaseModel):
    id: int
    memorial_id: int
    user_id: int
    user_email: str
    user_username: str
    requested_role: str
    message: Optional[str] = None
    status: str  # "pending" | "approved" | "rejected"
    created_at: datetime

    class Config:
        from_attributes = True


# Invite Schemas
class InviteCreate(BaseModel):
    label: Optional[str] = None
    expires_days: Optional[int] = None  # None = бессрочный
    expires_at: Optional[datetime] = None  # явная дата истечения (альтернатива expires_days)
    permissions: Optional[Dict] = None


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


# Live Avatar Session Schemas
class LiveSessionStartRequest(BaseModel):
    memorial_id: int
    language: str = "ru"  # "ru" | "en"


class LiveSessionStartResponse(BaseModel):
    session_id: str
    memorial_id: int
    sessions_used: int            # after this request
    sessions_limit: Optional[int] = None   # None = pool model (lifetime_pro)
    sessions_remaining: Optional[int] = None  # for pool model
    message: str


# Waitlist (landing)
class WaitlistSignupCreate(BaseModel):
    email: EmailStr
    source: Optional[str] = Field(None, max_length=64)


class WaitlistSignupResponse(BaseModel):
    ok: bool = True
    message: str
    already_registered: bool = False

