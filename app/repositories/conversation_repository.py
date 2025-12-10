from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation, ConversationParticipant
from app.db.models.message import Message


async def get_one_to_one_conversation(
    session: AsyncSession, user_a: str, user_b: str
) -> Conversation | None:
    try:
        sub = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id.in_([user_a, user_b]))
            .group_by(ConversationParticipant.conversation_id)
            .having(func.count(ConversationParticipant.user_id) == 2)
            .subquery()
        )

        query = select(Conversation).where(
            Conversation.conversation_id.in_(select(sub.c.conversation_id)),
            Conversation.is_group.is_(False),
        )
        result = await session.execute(query)
        conversation = result.scalars().first()

        return conversation

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def create_conversation_with_participants(
    session: AsyncSession, participants: list[str], is_group: bool = False
) -> Conversation:
    try:
        conversation = Conversation(
            is_group=is_group, created_at=datetime.now(timezone.utc)
        )
        session.add(conversation)
        await session.flush()

        rows = []
        for uid in participants:
            rows.append(
                ConversationParticipant(
                    conversation_id=conversation.conversation_id,
                    user_id=uid,
                    joined_at=datetime.now(timezone.utc),
                    last_read_message_id=None,
                    last_read_at=None,
                )
            )

        session.add_all(rows)
        await session.flush()

        return conversation

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def update_participant_read(
    session: AsyncSession,
    conversation_id: str,
    user_id: str,
    last_read_message_id: str | None,
) -> None:
    try:
        statement = (
            select(ConversationParticipant)
            .where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
            .limit(1)
        )

        result = await session.execute(statement)
        participant = result.scalars().first()

        if participant:
            participant.last_read_message_id = last_read_message_id
            participant.last_read_at = datetime.now(timezone.utc)
            session.add(participant)

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def get_user_conversations_with_last_message_and_unread_count(
    db: AsyncSession, user_id
):
    try:
        participants_statement = select(ConversationParticipant).where(
            ConversationParticipant.user_id == user_id
        )
        participants_response = await db.execute(participants_statement)
        participants = participants_response.scalars().all()

        result = []
        for participant in participants:
            conversation_statement = select(Conversation).where(
                Conversation.conversation_id == participant.conversation_id
            )
            conversation_response = await db.execute(conversation_statement)
            conversation = conversation_response.scalars().first()
            if conversation is None:
                continue

            last_message_statement = (
                select(Message)
                .where(Message.conversation_id == conversation.conversation_id)
                .order_by(Message.sent_at.desc())
                .limit(1)
            )
            last_message_response = await db.execute(last_message_statement)
            last_message = last_message_response.scalars().first()

            count_filters = [
                Message.conversation_id == conversation.conversation_id,
                Message.sender_id != user_id,
            ]
            if participant.last_read_at is not None:
                count_filters.append(
                    Message.sent_at > participant.last_read_at
                )

            count_statement = (
                select(func.count()).select_from(Message).where(*count_filters)
            )
            count_response = await db.execute(count_statement)
            count_message = count_response.scalar_one_or_none() or 0

            other_participant_id = None
            if conversation.is_group:
                other_participant_id = None
            else:
                # for 1-to-1 conversation, find the other user
                other_statement = (
                    select(ConversationParticipant)
                    .where(
                        ConversationParticipant.conversation_id
                        == conversation.conversation_id,
                        ConversationParticipant.user_id != user_id,
                    )
                    .limit(1)
                )
                other_response = await db.execute(other_statement)
                other = other_response.scalars().first()

                if other:
                    other_participant_id = other.user_id

            result.append(
                {
                    "conversation": conversation,
                    "last_message": last_message,
                    "unread_count": count_message,
                    "user_id": user_id,
                    "other_user_id": other_participant_id,
                }
            )

        return result

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
