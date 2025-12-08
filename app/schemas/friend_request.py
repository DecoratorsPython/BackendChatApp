from pydantic import BaseModel, EmailStr


class FriendRequestByEmail(BaseModel):
    email: EmailStr
