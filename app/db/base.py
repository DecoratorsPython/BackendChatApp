from sqlalchemy.orm import declarative_base

Base = declarative_base()

# importă modelele ca să le vadă Alembic
from app.db.models.user import User, Friendship  # noqa
from app.db.models.conversation import Conversation, ConversationParticipant  # noqa
from app.db.models.message import Message, MessageReceipt  # noqa
