from alembic import op

from app.db.base import Base

# revision identifiers, used by Alembic.
revision = "9edb02db3d3c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
