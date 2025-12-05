from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TEXT
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # profile
    username = Column(String(100), unique=False, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    avatar_url = Column(TEXT, nullable=True)

    # OAuth
    provider = Column(String(50), nullable=False)      # 'google'
    provider_sub = Column(String(255), nullable=False) # sub from Google

    # meta
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("provider", "provider_sub", name="uq_provider_identity"),
    )


class Friendship(Base):
    __tablename__ = "friendships"

    user_id_1 = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id_2 = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )

    status = Column(String(20), nullable=False)  # 'pending' | 'accepted' | 'blocked'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # the opaque refresh token string sent to the client
    token = Column(String(255), unique=True, nullable=False)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    expires_at = Column(
        DateTime,
        nullable=False,
    )

    # if not null → user or server has revoked that token
    revoked_at = Column(
        DateTime,
        nullable=True,
    )

    # used to trace chained refresh-token rotations
    rotated_from = Column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.token_id", ondelete="SET NULL"),
        nullable=True,
    )

    # optional: see all rotated tokens
    previous_token = relationship("RefreshToken", remote_side=[token_id])