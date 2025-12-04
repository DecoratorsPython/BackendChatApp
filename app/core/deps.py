# app/core/deps.py

from uuid import UUID
from types import SimpleNamespace

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models.user import User


def get_current_user(db: Session = Depends(get_db)):
    """
    TEMPORARY implementation, forces the current user to be Alice.
    Replace with real authentication logic later.

    """
    user = db.query(User).filter(User.email == "alice@test.com").first()

    if not user:
        
        raise Exception("User 'alice@test.com' does not exist in the DB.")

    return user
