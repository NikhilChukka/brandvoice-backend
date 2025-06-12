from logging.config import fileConfig
from pathlib import Path
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel
import sys
from dotenv import load_dotenv
from app.models import User, Schedule, ContentItem, Product  # Import all models to ensure they are registered with SQLAlchemy
from alembic import context
import os  # Ensure os module is imported
from app.core.config import get_settings

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))  
load_dotenv(project_root / ".env", override=False)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Explicitly set sqlalchemy.url from environment variable
database_url_from_env = os.getenv("DATABASE_URL")
if database_url_from_env:
    config.set_main_option("sqlalchemy.url", database_url_from_env)
    print(f"[DEBUG] Alembic sqlalchemy.url set from DATABASE_URL env var: {database_url_from_env}")
elif not config.get_main_option("sqlalchemy.url"):  # Check if it was set by other means (e.g. direct value in alembic.ini)
    raise ValueError(
        "DATABASE_URL environment variable is not set, and sqlalchemy.url is not configured directly in alembic.ini. "
        "Please set the DATABASE_URL environment variable or configure sqlalchemy.url in alembic.ini."
    )

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata
print("[DEBUG] tables registered:", list(target_metadata.tables))

settings = get_settings()
# Remove '+asyncpg' for sync migrations
sync_url = settings.database_url.replace("+asyncpg", "")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(sync_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
