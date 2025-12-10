from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    is_group = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_read_message_id = Column(UUID(as_uuid=True), nullable=True)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
