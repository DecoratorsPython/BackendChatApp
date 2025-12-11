import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.deps import get_db, get_current_user
from app.db.models.message import Message
from app.schemas.message_out import MessageOut
from app.db.models.user import User
from app.services.chat_service import mark_conversation_read


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
        conv_uuid = uuid.UUID(conversation_id)
    except Exception:
        return []

    try:
        await mark_conversation_read(
                db, conversation_id, current_user.user_id
            )

        statement = (
            select(Message)
            .where(Message.conversation_id == conv_uuid)
            .order_by(Message.sent_at.asc())
        )
        result = await db.execute(statement)
        messages = result.scalars().all()

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


@router.delete("/messages/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: str,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        msg_uuid = uuid.UUID(message_id)
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail="Invalid message ID"
        )from err

    try:
        result = await db.execute(
            select(Message).where(Message.message_id == msg_uuid)
        )
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        await db.delete(message)
        await db.commit()
        return {"detail": "Message deleted"}
    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )from err
