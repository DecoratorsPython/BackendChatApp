from datetime import datetime

from pydantic import BaseModel


class RefreshTokenData(BaseModel):
    token_id: str
    user_id: str
    expires_at: datetime
    revoked: bool
