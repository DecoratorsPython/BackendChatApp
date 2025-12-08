from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def safe_commit(session: Session) -> None:
    """
    Commit helper: if commit fails, rollback and raise 500.
    """
    try:
        session.commit()
    except SQLAlchemyError as err:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred. Please try again later.",
        ) from err
