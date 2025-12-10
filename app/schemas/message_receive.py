import uuid

from pydantic import BaseModel


class MessageReceive(BaseModel):
    user_id: uuid.UUID
    content: str
