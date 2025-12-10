from fastapi import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.repositories.conversation_repository import get_user_conversations_with_last_message_and_unread_count
from app.core.deps import get_db, get_current_user
from app.db.models.user import User
from app.schemas.message_out import MessageOut
from app.schemas.conversation_out import ConversationOut
from app.db.models.message import Message
from app.schemas.message_out import MessageOut
router = APIRouter()

@router.get("/conversations/me", response_model=List[ConversationOut])
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversations = get_user_conversations_with_last_message_and_unread_count(db, current_user.user_id)
    result = []
    for conv_meta in conversations:
        conv = conv_meta['conversation']
        last_msg = conv_meta['last_message']
        other_user_id = conv_meta.get('other_user_id')
        participant_name = None
        participant_email = None
        participant_avatar = None
        participant_last_seen = None
        last_message_time = last_msg.sent_at.isoformat() if last_msg else None

        if other_user_id:
            from app.db.models.user import User
            participant = db.query(User).filter(User.user_id == other_user_id).first()
            if participant:
                participant_name = participant.username
                participant_email = participant.email
                participant_avatar = participant.avatar_url
                participant_last_seen = participant.last_login.isoformat() if participant.last_login else None

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
                last_message_time=last_message_time,
                unread_count=conv_meta['unread_count'],
                other_user_id=str(other_user_id) if other_user_id is not None else None,
                participant_name=participant_name,
                participant_email=participant_email,
                participant_avatar=participant_avatar,
                participant_last_seen=participant_last_seen
            )
        )
    return result


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.sent_at.asc()).all()
    if not messages:
        return []
    return [
        MessageOut(
            message_id=str(msg.message_id),
            content=msg.content,
            sent_at=msg.sent_at.isoformat()
        ) for msg in messages
    ]