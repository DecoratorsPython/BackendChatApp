from pydantic import BaseModel

from app.schemas.message_out import MessageOut


class ConversationOut(BaseModel):
    conversation_id: str
    is_group: bool
    created_at: str
    last_message: MessageOut | None
    unread_count: int
