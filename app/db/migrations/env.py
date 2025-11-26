from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.base import Base  # Base cu toate modelele tale

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# <<< AICI îi dăm lui Alembic metadata-ul modelelor tale >>>
target_metadata = Base.metadata

print("ALEMBIC ENV: tables =", list(target_metadata.tables.keys()))

print("ALEMBIC ENV: running migrations...")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In this mode we don't need a DB connection; Alembic va genera SQL.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Aici ne conectăm la DB și rulăm efectiv migrațiile.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
