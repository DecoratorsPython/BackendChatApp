from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.session import SessionLocal
from app.repositories.conversation_repository import (
    get_one_to_one_conversation,
    update_participant_read,
)
from app.repositories.message_repository import (
    create_message,
    create_message_receipts,
    get_latest_message_in_conversation,
    mark_messages_seen,
)


async def verify_one_to_one_conversation(
    session: AsyncSession, user_a: str, user_b: str
) -> Conversation:
    try:
        conversation = await get_one_to_one_conversation(
            session, user_a, user_b
        )

        return bool(conversation)

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def persist_outgoing_message(
    sender_id: str, recipient_id: str, content: str, conversation_id: str
) -> None:
    async with SessionLocal() as session:
        try:
            async with session.begin():
                message = await create_message(
                    session, conversation_id, sender_id, content
                )
                recipient_ids = [recipient_id]

                await create_message_receipts(
                    session, message.message_id, recipient_ids
                )

        except SQLAlchemyError as err:
            raise RuntimeError("Database error occurred") from err


async def mark_conversation_read(
    session: AsyncSession, conversation_id: str, user_id: str
) -> None:
    try:
        await mark_messages_seen(session, conversation_id, user_id)

        latest = await get_latest_message_in_conversation(
            session, conversation_id
        )

        if latest:
            await update_participant_read(
                session,
                conversation_id,
                user_id,
                str(latest.message_id),
            )

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
