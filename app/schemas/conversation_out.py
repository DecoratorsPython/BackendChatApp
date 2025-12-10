from pydantic import BaseModel

from app.schemas.message_out import MessageOut


class ConversationOut(BaseModel):
    conversation_id: str
    is_group: bool
    created_at: str
    last_message: MessageOut | None
    last_message_time: str | None = None
    unread_count: int
    other_user_id: str | None = None
    participant_name: str | None = None
    participant_email: str | None = None
    participant_avatar: str | None = None
    participant_last_seen: str | None = None
