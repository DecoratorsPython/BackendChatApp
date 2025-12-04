from pydantic import BaseModel

class MessageOut(BaseModel):
    message_id: str
    content: str
    sent_at: str
