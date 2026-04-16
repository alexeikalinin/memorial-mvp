"""
SQLAlchemy модели для базы данных.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, UniqueConstraint, JSON, Index
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db import Base


class MediaType(str, enum.Enum):
    """Типы медиа-файлов."""
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class UserRole(str, enum.Enum):
    """Роли пользователей для доступа к мемориалу."""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class SubscriptionPlan(str, enum.Enum):
    """Тарифный план пользователя."""
    FREE = "free"
    PLUS = "plus"
    LIFETIME = "lifetime"


class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # nullable для Google-only юзеров
    full_name = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    # Subscription / billing
    subscription_plan = Column(String(20), default="free", nullable=False, server_default="free")
    plan_expires_at = Column(DateTime(timezone=True), nullable=True)   # None = free or lifetime (no expiry)
    lifetime_memorial_id = Column(Integer, nullable=True)               # Locked memorial for lifetime plan
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    memorials = relationship("Memorial", back_populates="owner", cascade="all, delete-orphan")
    memorial_access = relationship("MemorialAccess", foreign_keys="MemorialAccess.user_id", back_populates="user")


class Memorial(Base):
    """Модель мемориала (страница памяти о человеке)."""
    __tablename__ = "memorials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    birth_date = Column(DateTime(timezone=True), nullable=True)
    death_date = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=False)
    voice_id = Column(String(255), nullable=True)  # ID кастомного голоса в ElevenLabs
    voice_gender = Column(String(20), nullable=True)  # 'male' | 'female' — для выбора голоса по полу, если нет клона
    cover_photo_id = Column(Integer, ForeignKey("media.id"), nullable=True)  # ID фото обложки
    language = Column(String(5), default="ru", nullable=False, server_default="ru")  # "ru" | "en"
    tree_layout_json = Column(JSON, nullable=True)  # {"nodePositions": {"memId": {"x": 0, "y": 0}}, "version": 1}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    owner = relationship("User", back_populates="memorials")
    media = relationship(
        "Media",
        foreign_keys="[Media.memorial_id]",
        back_populates="memorial",
        cascade="all, delete-orphan",
    )
    memories = relationship("Memory", back_populates="memorial", cascade="all, delete-orphan")
    relationships_from = relationship("FamilyRelationship", foreign_keys="FamilyRelationship.memorial_id", back_populates="memorial", cascade="all, delete-orphan")
    relationships_to = relationship("FamilyRelationship", foreign_keys="FamilyRelationship.related_memorial_id", back_populates="related_memorial", cascade="all, delete-orphan")
    invites = relationship("MemorialInvite", back_populates="memorial", cascade="all, delete-orphan")
    access_entries = relationship("MemorialAccess", back_populates="memorial", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="memorial", cascade="all, delete-orphan")


class Media(Base):
    """Модель медиа-файла (фото, видео, аудио)."""
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)  # Локальный путь или S3 ключ
    file_url = Column(String(1000), nullable=True)  # Публичный URL
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # Размер в байтах
    mime_type = Column(String(100), nullable=True)
    media_type = Column(Enum(MediaType), nullable=False, index=True)
    thumbnail_path = Column(String(500), nullable=True)  # Путь к миниатюре
    is_animated = Column(Boolean, default=False)  # Флаг для оживленных фото
    animation_task_id = Column(String(255), nullable=True)  # ID задачи анимации
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    memorial = relationship(
        "Memorial",
        foreign_keys="[Media.memorial_id]",
        back_populates="media",
    )


class Memory(Base):
    """Модель воспоминания (текстовый фрагмент для RAG)."""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)  # Текст воспоминания
    embedding_id = Column(String(255), nullable=True)  # ID вектора в Pinecone
    source = Column(String(100), nullable=True)  # Источник: "user", "document", "transcription"
    event_date = Column(DateTime(timezone=True), nullable=True)  # Дата события в воспоминании
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    memorial = relationship("Memorial", back_populates="memories")


class RelationshipType(str, enum.Enum):
    """Типы семейных связей."""
    PARENT          = "parent"           # Биологический родитель
    CHILD           = "child"            # Биологический ребёнок
    SPOUSE          = "spouse"           # Супруг/супруга (в браке)
    SIBLING         = "sibling"          # Родной брат/сестра
    STEP_PARENT     = "step_parent"      # Отчим/мачеха
    STEP_CHILD      = "step_child"       # Пасынок/падчерица
    ADOPTIVE_PARENT = "adoptive_parent"  # Усыновитель/удочеритель
    ADOPTIVE_CHILD  = "adoptive_child"   # Усыновлённый/удочерённая
    HALF_SIBLING    = "half_sibling"     # Единокровный/единоутробный брат/сестра
    PARTNER         = "partner"          # Гражданский партнёр (без брака)
    EX_SPOUSE       = "ex_spouse"        # Бывший супруг/супруга
    CUSTOM          = "custom"           # Произвольная связь (задаётся вручную)


class RelationshipTypeColumn(TypeDecorator):
    """
    Хранит строку .value в БД. Читает и нижний регистр (seed, API), и легаси-имена SQLAlchemy Enum (PARENT).
    """
    impl = String(32)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, RelationshipType):
            return value.value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        s = str(value).strip()
        try:
            return RelationshipType(s)
        except ValueError:
            pass
        key = s.upper()
        if key in RelationshipType.__members__:
            return RelationshipType[key]
        raise ValueError(f"Unknown relationship_type in DB: {value!r}")


class FamilyRelationship(Base):
    """Модель семейной связи между мемориалами."""
    __tablename__ = "family_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False, index=True)
    related_memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False, index=True)
    relationship_type = Column(RelationshipTypeColumn(), nullable=False, index=True)
    custom_label = Column(String(100), nullable=True)  # Заполняется только для CUSTOM типа
    notes = Column(Text, nullable=True)  # Дополнительные заметки о связи
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    memorial = relationship("Memorial", foreign_keys=[memorial_id], back_populates="relationships_from")
    related_memorial = relationship("Memorial", foreign_keys=[related_memorial_id], back_populates="relationships_to")
    
    # Уникальность: одна связь одного типа между двумя мемориалами
    __table_args__ = (
        UniqueConstraint('memorial_id', 'related_memorial_id', 'relationship_type', name='uq_relationship'),
        Index('ix_family_rel_memorial_type', 'memorial_id', 'relationship_type'),
    )


class MemorialInvite(Base):
    """Инвайт-токен для доступа родственников к мемориалу без регистрации."""
    __tablename__ = "memorial_invites"

    id = Column(Integer, primary_key=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    label = Column(String(100), nullable=True)  # "Папа", "Тётя Маша"
    permissions = Column(JSON, default={"add_memories": True, "chat": True, "view_media": True})
    expires_at = Column(DateTime(timezone=True), nullable=True)  # None = бессрочный
    uses_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    memorial = relationship("Memorial", back_populates="invites")


class AccessRequestStatus(str, enum.Enum):
    """Статус запроса доступа к мемориалу."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccessRequest(Base):
    """Запрос пользователя на получение доступа к мемориалу."""
    __tablename__ = "access_requests"

    id             = Column(Integer, primary_key=True, index=True)
    memorial_id    = Column(Integer, ForeignKey("memorials.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    message        = Column(Text, nullable=True)
    status         = Column(Enum(AccessRequestStatus), default=AccessRequestStatus.PENDING, nullable=False, index=True)
    reviewed_by    = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at    = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    memorial = relationship("Memorial", back_populates="access_requests")
    user     = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        UniqueConstraint("memorial_id", "user_id", name="uq_access_request"),
    )


class MemorialAccess(Base):
    """Доступ пользователя к мемориалу с определённой ролью."""
    __tablename__ = "memorial_access"

    id          = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role        = Column(Enum(UserRole), nullable=False)   # OWNER | EDITOR | VIEWER
    granted_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    memorial = relationship("Memorial", back_populates="access_entries")
    user     = relationship("User", foreign_keys=[user_id], back_populates="memorial_access")
    granter  = relationship("User", foreign_keys=[granted_by])

    __table_args__ = (
        UniqueConstraint("memorial_id", "user_id", name="uq_memorial_access"),
    )


class WaitlistSignup(Base):
    """Email для уведомления о запуске полного функционала (лендинг / waitlist)."""
    __tablename__ = "waitlist_signups"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    source = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserUsage(Base):
    """Счётчики использования AI-фич пользователем за расчётный период (месяц)."""
    __tablename__ = "user_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period = Column(String(7), nullable=False)  # "2026-04" — год-месяц UTC
    chat_messages = Column(Integer, default=0, nullable=False)
    animations = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "period", name="uq_user_usage_period"),
        Index("ix_user_usage_user_period", "user_id", "period"),
    )

