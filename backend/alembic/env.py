import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool, create_engine

# Добавляем корень backend в PYTHONPATH для alembic CLI
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.config import DATABASE_URL
from src.db.tables import Base

# Синхронный URL для alembic (psycopg2 вместо asyncpg)
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")

config = context.config
config.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

local_env = Path(__file__).resolve().parent.parent.parent.parent / ".env.local"
if local_env.exists():
    load_dotenv(local_env, override=True)


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме (--sql)."""
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций через синхронный psycopg2 engine."""
    connectable = create_engine(SYNC_DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
