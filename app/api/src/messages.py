# Endpoints related to message operations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_user
from app.db.models.message import Message
from app.schemas.message_out import MessageOut
from app.db.models.user import User

router = APIRouter()


@router.get("/messages/{conversation_id}", response_model=List[MessageOut])
def get_messages_for_conversation(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	import uuid
	try:
		conv_uuid = uuid.UUID(conversation_id)
	except Exception:
		return []
	messages = db.query(Message).filter(Message.conversation_id == conv_uuid).order_by(Message.sent_at.asc()).all()
	return [
		MessageOut(
			message_id=str(msg.message_id),
			sender_id=str(msg.sender_id),
			content=msg.content,
			sent_at=msg.sent_at.isoformat()
		) for msg in messages
	]
