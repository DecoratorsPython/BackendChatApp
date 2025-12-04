# Conversation repository
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.conversation import Conversation, ConversationParticipant
from app.db.models.message import Message

def get_user_conversations_with_last_message_and_unread_count(db: Session, user_id):
    participants = (
        db.query(ConversationParticipant)
        .filter(ConversationParticipant.user_id == user_id)
        .all()
    )
    result = []
    for participant in participants:
        conv = db.query(Conversation).filter(Conversation.conversation_id == participant.conversation_id).first()
        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == conv.conversation_id)
            .order_by(Message.sent_at.desc())
            .first()
        )
        unread_count = db.query(Message).filter(
            Message.conversation_id == conv.conversation_id,
            Message.sender_id != user_id,
            or_(
                participant.last_read_at == None,
                Message.sent_at > participant.last_read_at
            )
        ).count()
        result.append({
            'conversation': conv,
            'last_message': last_msg,
            'unread_count': unread_count,
            'user_id': user_id
        })
    return result
