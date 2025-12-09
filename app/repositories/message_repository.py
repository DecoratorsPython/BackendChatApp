from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.message import Message, MessageReceipt


async def create_message(
    session: AsyncSession, conversation_id: str, sender_id: str, content: str
) -> Message:
    try:
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            sent_at=datetime.now(timezone.utc),
            read_at=None,
        )

        session.add(message)
        await session.flush()

        return message

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def create_message_receipts(
    session: AsyncSession, message_id: str, recipient_ids: list[str]
) -> None:
    try:
        rows = []
        for uid in recipient_ids:
            rows.append(
                MessageReceipt(
                    message_id=message_id,
                    user_id=uid,
                    delivered_at=datetime.now(timezone.utc),
                    seen_at=None,
                )
            )

        session.add_all(rows)
        await session.flush()

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def mark_messages_seen(
    session: AsyncSession, conversation_id: str, user_id: str
) -> None:
    try:
        query = (
            select(Message.message_id)
            .where(Message.conversation_id == conversation_id)
            .subquery()
        )

        recipient_statement = (
            update(MessageReceipt)
            .where(
                MessageReceipt.message_id.in_(select(query.c.message_id)),
                MessageReceipt.user_id == user_id,
                MessageReceipt.seen_at.is_(None),
            )
            .values(seen_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session=False)
        )

        await session.execute(recipient_statement)

        sender_statement = (
            update(Message)
            .where(
                Message.message_id.in_(select(query.c.message_id)),
                Message.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session=False)
        )

        await session.execute(sender_statement)

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def get_latest_message_in_conversation(
    session: AsyncSession, conversation_id: str
) -> Message | None:
    try:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.desc())
            .limit(1)
        )

        result = await session.execute(statement)
        message = result.scalars().first()

        return message

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
