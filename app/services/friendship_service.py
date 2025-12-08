from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from app.repositories import friendship_repository

def send_friend_request(db: Session, current_user_id: UUID, target_user_id: UUID):
    if current_user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself."
        )

    existing = friendship_repository.get_friendship(db, current_user_id, target_user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A relationship with status '{existing.status}' already exists."
        )

    friendship = friendship_repository.create_friend_request(db, current_user_id, target_user_id)
    return friendship
