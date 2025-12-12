from alembic import op

from app.db.base import Base

from app.db.models.user import User
from app.db.models.message import Message
from app.db.models.conversation import Conversation  


revision: str = '9e7c59db3c5c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)