from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class FriendRequestByEmail(BaseModel):
    email: EmailStr


class FriendshipBase(BaseModel):
    user_id: UUID


class FriendshipResponse(BaseModel):
    user_id_1: UUID
    user_id_2: UUID
    status: str
    created_at: datetime
    accepted_at: datetime | None = None

    class Config:
        from_attributes = True 
