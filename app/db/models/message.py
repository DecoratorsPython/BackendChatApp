from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    content = Column(Text, nullable=False)
    sent_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    read_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_messages_conversation_time", "conversation_id", "sent_at"),
        Index(
            "idx_messages_conversation_sender_time",
            "conversation_id",
            "sender_id",
            "sent_at",
        ),
    )


class MessageReceipt(Base):
    __tablename__ = "message_receipts"

    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )

    delivered_at = Column(DateTime(timezone=True), nullable=True)
    seen_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_receipts_user_seen", "user_id", "seen_at"),
        Index("idx_receipts_message", "message_id"),
    )
