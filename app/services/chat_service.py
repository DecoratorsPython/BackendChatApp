from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.session import async_session
from app.repositories.conversation_repository import (
    create_conversation_with_participants,
    get_one_to_one_conversation,
)
from app.repositories.message_repository import (
    create_message,
    create_message_receipts,
)


async def ensure_one_to_one_conversation(
    session: AsyncSession, user_a: str, user_b: str
) -> Conversation:
    conversation = await get_one_to_one_conversation(session, user_a, user_b)
    if conversation:
        return conversation
    return await create_conversation_with_participants(
        session, [user_a, user_b], is_group=False
    )


async def persist_outgoing_message(
    sender_id: str,
    recipient_id: str,
    content: str,
    conversation_id: str | None = None,
) -> dict:
    async with async_session() as session, session.begin():
        if conversation_id is None:
            conversation = await ensure_one_to_one_conversation(
                session, sender_id, recipient_id
            )
            conversation_id = str(conversation.conversation_id)
        else:
            conversation_id = str(conversation_id)

        message = await create_message(
            session, conversation_id, sender_id, content
        )
        recipient_ids = [recipient_id]
        await create_message_receipts(
            session, message.message_id, recipient_ids
        )

    return str(message.message_id), conversation_id


# async def mark_conversation_read(conversation_id: str, user_id: str) -> int:
#     async with async_session() as session, session.begin():
#         updated = await mark_messages_seen(session, conversation_id, user_id)
#         latest_query = await session.execute(
#             select(
#                 Message := __import__(
#                     "app.db.models.message", fromlist=["Message"]
#                 ).Message
#             )
#             .where(Message.conversation_id == conversation_id)
#             .order_by(Message.sent_at.desc())
#             .limit(1)
#         )

#         latest = latest_query.scalars().first()
#         if latest:
#             await update_participant_read(
#                 session, conversation_id, user_id, str(latest.message_id)
#             )

#     return updated
