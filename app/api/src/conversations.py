# Endpoints related to conversations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.repositories.conversation_repository import get_user_conversations_with_last_message_and_unread_count
from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from pydantic import BaseModel

router = APIRouter()

class MessageOut(BaseModel):
    message_id: str
    content: str
    sent_at: str

class ConversationOut(BaseModel):
    conversation_id: str
    is_group: bool
    created_at: str
    last_message: MessageOut | None
    unread_count: int

@router.get("/conversations/me", response_model=List[ConversationOut])
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversations = get_user_conversations_with_last_message_and_unread_count(db, current_user.user_id)
    result = []
    for conv_meta in conversations:
        conv = conv_meta.conversation
        last_msg = conv_meta.last_message
        result.append(
            ConversationOut(
                conversation_id=str(conv.conversation_id),
                is_group=conv.is_group,
                created_at=conv.created_at.isoformat(),
                last_message=MessageOut(
                    message_id=str(last_msg.message_id),
                    content=last_msg.content,
                    sent_at=last_msg.sent_at.isoformat(),
                ) if last_msg else None,
                unread_count=conv_meta.unread_count
            )
        )
    return result
