from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.deps import get_db
from app.db.models.message import Message
from app.db.models.user import User
from app.repositories.conversation_repository import (
    create_conversation_with_participants,
    get_one_to_one_conversation,
    get_user_conversations_with_last_message_and_unread_count,
)
from app.schemas.conversation_out import ConversationOut
from app.schemas.message_out import MessageOut
from app.services.chat_service import (
    mark_conversation_read,
    verify_one_to_one_conversation,
)

router = APIRouter()

get_db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.get("/conversations/exists")
async def check_one_to_one_conversation_exists(
    other_user_id: str,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        async with db.begin():
            value = await verify_one_to_one_conversation(
                db, current_user.user_id, other_user_id
            )

            return value

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.post("conversations/create")
async def create_one_to_one_conversation(
    other_user_id: str,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        async with db.begin():
            value = await create_conversation_with_participants(
                db, [current_user.user_id, other_user_id], is_group=False
            )

            return value

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.get("/conversations/receive")
async def obtain_one_to_one_conversation(
    other_user_id: str,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        async with db.begin():
            value = await get_one_to_one_conversation(
                db, current_user.user_id, other_user_id
            )

            return value

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


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
                other_user_id = conv_meta.get("other_user_id")
                participant_name = None
                participant_email = None
                participant_avatar = None
                participant_last_seen = None
                last_message_time = (
                    last_msg.sent_at.isoformat() if last_msg else None
                )

                if other_user_id:
                    statement = select(User).where(
                        User.user_id == other_user_id
                    )
                    response = await db.execute(statement)
                    participant = response.scalar_one_or_none()
                    if participant:
                        participant_name = participant.username
                        participant_email = participant.email
                        participant_avatar = participant.avatar_url
                        participant_last_seen = (
                            participant.last_login.isoformat()
                            if participant.last_login
                            else None
                        )

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
                        last_message_time=last_message_time,
                        unread_count=conv_meta["unread_count"],
                        other_user_id=(
                            str(other_user_id)
                            if other_user_id is not None
                            else None
                        ),
                        participant_name=participant_name,
                        participant_email=participant_email,
                        participant_avatar=participant_avatar,
                        participant_last_seen=participant_last_seen,
                    )
                )

            return result

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageOut],
)
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        async with db.begin():
            await mark_conversation_read(
                db, conversation_id, current_user.user_id
            )

            statement = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.sent_at.asc())
            )
            result = await db.execute(statement)
            messages = result.scalars().all()

            if not messages:
                return []

            return [
                MessageOut(
                    message_id=str(msg.message_id),
                    content=msg.content,
                    sent_at=msg.sent_at.isoformat(),
                )
                for msg in messages
            ]

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
