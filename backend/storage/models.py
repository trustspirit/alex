from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from backend.storage.database import Base


# Association table for Document <-> Tag many-to-many
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents = relationship("Document", back_populates="collection")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_path = Column(String, nullable=False)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True)
    status = Column(String, default="pending", nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    fallback_used = Column(Boolean, default=False, nullable=False)
    fallback_warning = Column(Text, nullable=True)
    sync_status = Column(String, default="pending")
    synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    collection = relationship("Collection", back_populates="documents")
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    documents = relationship("Document", secondary=document_tags, back_populates="tags")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    title = Column(String, default="New Chat", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source_references = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=True)
    encrypted = Column(Boolean, default=False, nullable=False)


class SyncState(Base):
    __tablename__ = "sync_state"
    id = Column(String, primary_key=True)
    last_pull_at = Column(DateTime, nullable=True)
    last_push_at = Column(DateTime, nullable=True)
    r2_manifest_etag = Column(String, nullable=True)


class PendingSync(Base):
    __tablename__ = "pending_sync"
    id = Column(String, primary_key=True)
    doc_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    retry_count = Column(Integer, default=0)
