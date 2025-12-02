from app.db.base import get_db
from app.db.models.user import User

def print_all_users():
    db = next(get_db())
    users = db.query(User).all()
    for user in users:
        print(
            f"user_id: {user.user_id}, username: {user.username}, email: {user.email}, "
            f"avatar_url: {user.avatar_url}, provider: {user.provider}, "
            f"provider_sub: {user.provider_sub}, created_at: {user.created_at}, last_login: {user.last_login}"
        )

if __name__ == "__main__":
    print_all_users()
