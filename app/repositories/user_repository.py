from sqlalchemy.orm import Session
from app.db.models.user import User


def get_user_by_email(session: Session, email: str) -> User | None:
    """
    Return a user by email, or None if not found.
    """
    return session.query(User).filter(User.email == email).first()
