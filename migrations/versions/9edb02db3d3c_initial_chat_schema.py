from alembic import op
import sqlalchemy as sa

# ADD THESE IMPORTS:
from sqlalchemy import create_engine
from app.db.base import Base

# revision identifiers, used by Alembic.
revision = '9edb02db3d3c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE ENGINE – adapt URL dacă ai alt port/user/pass/db
    engine = create_engine(
        "postgresql+psycopg2://chat_user:chat_pass@localhost:5433/chat_dev",
        future=True
    )

    # CREEAZĂ TOATE TABELELE DEFINITE ÎN MODELE
    Base.metadata.create_all(bind=engine)


def downgrade() -> None:
    engine = create_engine(
        "postgresql+psycopg2://chat_user:chat_pass@localhost:5433/chat_dev",
        future=True
    )
    # Optional: șterge toate tabelele
    Base.metadata.drop_all(bind=engine)
