from pydantic import BaseModel
from datetime import datetime


class RefreshTokenData(BaseModel):
    token_id: str
    user_id: str
    expires_at: datetime
    revoked: bool

class RefreshRequest(BaseModel):
    refresh_token: str
