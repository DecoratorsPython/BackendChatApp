import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.deps import get_db, get_current_user
from app.db.models.message import Message
from app.schemas.message_out import MessageOut
from app.db.models.user import User
from app.services.chat_service import mark_conversation_read
from app.repositories.message_repository import get_message_history

router = APIRouter()

get_db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.get("/messages/{conversation_id}", response_model=List[MessageOut])
async def get_messages_for_conversation(
    conversation_id: str,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        await mark_conversation_read(
                conversation_id, current_user.user_id
            )

        messages = await get_message_history(conversation_id)

        return [
            MessageOut(
                message_id=str(msg.message_id),
                sender_id=str(msg.sender_id),
                content=msg.content,
                sent_at=msg.sent_at.isoformat(),
            )
            for msg in messages
        ]

    except SQLAlchemyError:
        return []