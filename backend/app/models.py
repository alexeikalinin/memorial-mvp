"""
SQLAlchemy модели для базы данных.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, UniqueConstraint
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


class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    memorials = relationship("Memorial", back_populates="owner", cascade="all, delete-orphan")


class Memorial(Base):
    """Модель мемориала (страница памяти о человеке)."""
    __tablename__ = "memorials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    birth_date = Column(DateTime(timezone=True), nullable=True)
    death_date = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    voice_id = Column(String(255), nullable=True)  # ID кастомного голоса в ElevenLabs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    owner = relationship("User", back_populates="memorials")
    media = relationship("Media", back_populates="memorial", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="memorial", cascade="all, delete-orphan")
    relationships_from = relationship("FamilyRelationship", foreign_keys="FamilyRelationship.memorial_id", back_populates="memorial", cascade="all, delete-orphan")
    relationships_to = relationship("FamilyRelationship", foreign_keys="FamilyRelationship.related_memorial_id", back_populates="related_memorial", cascade="all, delete-orphan")


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
    memorial = relationship("Memorial", back_populates="media")


class Memory(Base):
    """Модель воспоминания (текстовый фрагмент для RAG)."""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)  # Текст воспоминания
    embedding_id = Column(String(255), nullable=True)  # ID вектора в Pinecone
    source = Column(String(100), nullable=True)  # Источник: "user", "document", "transcription"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    memorial = relationship("Memorial", back_populates="memories")


class RelationshipType(str, enum.Enum):
    """Типы семейных связей."""
    PARENT = "parent"  # Родитель
    CHILD = "child"    # Ребенок
    SPOUSE = "spouse"  # Супруг/супруга
    SIBLING = "sibling"  # Брат/сестра


class FamilyRelationship(Base):
    """Модель семейной связи между мемориалами."""
    __tablename__ = "family_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False, index=True)
    related_memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False, index=True)
    relationship_type = Column(Enum(RelationshipType), nullable=False, index=True)
    notes = Column(Text, nullable=True)  # Дополнительные заметки о связи
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    memorial = relationship("Memorial", foreign_keys=[memorial_id], back_populates="relationships_from")
    related_memorial = relationship("Memorial", foreign_keys=[related_memorial_id], back_populates="relationships_to")
    
    # Уникальность: одна связь одного типа между двумя мемориалами
    __table_args__ = (
        UniqueConstraint('memorial_id', 'related_memorial_id', 'relationship_type', name='uq_relationship'),
    )

