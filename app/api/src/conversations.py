# Endpoints related to conversations

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.deps import get_db
from app.db.models.user import User
from app.repositories.conversation_repository import (
    get_user_conversations_with_last_message_and_unread_count,
)
from app.schemas.conversation_out import ConversationOut
from app.schemas.message_out import MessageOut

router = APIRouter()

get_db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.get("/conversations/me", response_model=list[ConversationOut])
async def get_my_conversations(
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        async with db.begin():
            conversations = await (
                get_user_conversations_with_last_message_and_unread_count(
                    db, current_user.user_id
                )
            )
            result = []

            for conv_meta in conversations:
                conv = conv_meta["conversation"]
                last_msg = conv_meta["last_message"]

                result.append(
                    ConversationOut(
                        conversation_id=str(conv.conversation_id),
                        is_group=conv.is_group,
                        created_at=conv.created_at.isoformat(),
                        last_message=(
                            MessageOut(
                                message_id=str(last_msg.message_id),
                                content=last_msg.content,
                                sent_at=last_msg.sent_at.isoformat(),
                            )
                            if last_msg
                            else None
                        ),
                        unread_count=conv_meta["unread_count"],
                    )
                )

            return result

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
