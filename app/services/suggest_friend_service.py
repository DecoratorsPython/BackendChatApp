import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import Friendship, User


async def suggest_friends_for_user(db: AsyncSession, user_id):
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    # Get all accepted friends (bidirectional)
    statement = select(Friendship).where(
        ((Friendship.user_id_1 == user_id) | (Friendship.user_id_2 == user_id))
        & (Friendship.status == "accepted")
    )
    response = await db.execute(statement)
    direct_friends = response.scalars().all()

    friend_ids = set()
    for f in direct_friends:
        if f.user_id_1 == user_id:
            friend_ids.add(f.user_id_2)
        else:
            friend_ids.add(f.user_id_1)

    # Get all users with pending requests (sent or received)
    statement = select(Friendship).where(
        ((Friendship.user_id_1 == user_id) | (Friendship.user_id_2 == user_id))
        & (Friendship.status == "pending")
    )
    result = await db.execute(statement)
    pendings = result.scalars().all()

    pending_ids = set()
    for p in pendings:
        if p.user_id_1 == user_id:
            pending_ids.add(p.user_id_2)
        else:
            pending_ids.add(p.user_id_1)

    # Get friends of friends (bidirectional)
    fof_ids = set()
    for fid in friend_ids:
        # Friends where fid is user_id_1
        statement = select(Friendship).where(
            (Friendship.user_id_1 == fid) & (Friendship.status == "accepted")
        )
        result = await db.execute(statement)
        f1 = result.scalars().all()
        for f in f1:
            fof_ids.add(f.user_id_2)

        # Friends where fid is user_id_2
        statement = select(Friendship).where(
            (Friendship.user_id_2 == fid) & (Friendship.status == "accepted")
        )
        result = await db.execute(statement)
        f2 = result.scalars().all()
        for f in f2:
            fof_ids.add(f.user_id_1)

    # Exclude self, direct friends, and pending requests
    fof_ids.discard(user_id)
    fof_ids -= friend_ids
    fof_ids -= pending_ids

    if not fof_ids:
        return []

    statement = select(User).where(User.user_id.in_(fof_ids))
    result = await db.execute(statement)
    suggestions = result.scalars().all()
    return suggestions
