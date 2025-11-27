from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.db.models.user import User, Friendship  
from app.db.models.conversation import Conversation, ConversationParticipant  
from app.db.models.message import Message, MessageReceipt  
