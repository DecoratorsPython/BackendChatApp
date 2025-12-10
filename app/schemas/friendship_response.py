from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FriendshipResponse(BaseModel):
    user_id_1: UUID
    user_id_2: UUID
    status: str
    created_at: datetime
    accepted_at: datetime | None = None

    class Config:
        from_attributes = True
