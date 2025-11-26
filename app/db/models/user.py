# app/db/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TEXT
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # profil
    username = Column(String(100), unique=False, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    avatar_url = Column(TEXT, nullable=True)

    # OAuth
    provider = Column(String(50), nullable=False)      # ex: 'google'
    provider_sub = Column(String(255), nullable=False) # sub de la Google

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