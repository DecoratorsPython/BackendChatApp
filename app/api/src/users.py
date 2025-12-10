# Endpoints related to users
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.db.models.user import User

router = APIRouter(tags=["users"])

get_db_dependency = Depends(get_current_user)


@router.get("/users/me")
def get_me(current_user: User = get_db_dependency):
    return {
        "user_id": str(current_user.user_id),
        "username": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "provider": current_user.provider,
        "last_login": current_user.last_login,
    }
