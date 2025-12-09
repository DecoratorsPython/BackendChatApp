import uuid
from sqlalchemy.orm import Session
from app.db.models.user import User, Friendship


def suggest_friends_for_user(db: Session, user_id):
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    # Get all accepted friends (bidirectional)
    direct_friends = db.query(Friendship).filter(
        ((Friendship.user_id_1 == user_id) | (Friendship.user_id_2 == user_id)) &
        (Friendship.status == "accepted")
    ).all()
    friend_ids = set()
    for f in direct_friends:
        if f.user_id_1 == user_id:
            friend_ids.add(f.user_id_2)
        else:
            friend_ids.add(f.user_id_1)

    # Get all users with pending requests (sent or received)
    pending_ids = set()
    pendings = db.query(Friendship).filter(
        ((Friendship.user_id_1 == user_id) | (Friendship.user_id_2 == user_id)) &
        (Friendship.status == "pending")
    ).all()
    for p in pendings:
        if p.user_id_1 == user_id:
            pending_ids.add(p.user_id_2)
        else:
            pending_ids.add(p.user_id_1)

    # Get friends of friends (bidirectional)
    fof_ids = set()
    for fid in friend_ids:
        # Friends where fid is user_id_1
        f1 = db.query(Friendship).filter(
            (Friendship.user_id_1 == fid) & (Friendship.status == "accepted")
        ).all()
        for f in f1:
            fof_ids.add(f.user_id_2)
        # Friends where fid is user_id_2
        f2 = db.query(Friendship).filter(
            (Friendship.user_id_2 == fid) & (Friendship.status == "accepted")
        ).all()
        for f in f2:
            fof_ids.add(f.user_id_1)

    # Exclude self, direct friends, and pending requests
    fof_ids.discard(user_id)
    fof_ids -= friend_ids
    fof_ids -= pending_ids

    if not fof_ids:
        return []

    suggestions = db.query(User).filter(User.user_id.in_(fof_ids)).all()
    return suggestions
