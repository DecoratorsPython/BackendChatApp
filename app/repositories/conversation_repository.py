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
        if participant.last_read_at is None:
            unread_count = db.query(Message).filter(
                Message.conversation_id == conv.conversation_id,
                Message.sender_id != user_id
            ).count()
        else:
            unread_count = db.query(Message).filter(
                Message.conversation_id == conv.conversation_id,
                Message.sender_id != user_id,
                Message.sent_at > participant.last_read_at
            ).count()

        other_participant_id = None
        if conv.is_group:
            # for group conversation - for future use cases
            other_participant_id = None
        else:
            # for 1-to-1 conversation, find the other user
            other = db.query(ConversationParticipant).filter(
                ConversationParticipant.conversation_id == conv.conversation_id,
                ConversationParticipant.user_id != user_id
            ).first()
            if other:
                other_participant_id = other.user_id
        result.append({
            'conversation': conv,
            'last_message': last_msg,
            'unread_count': unread_count,
            'user_id': user_id,
            'other_user_id': other_participant_id
        })
    return result
