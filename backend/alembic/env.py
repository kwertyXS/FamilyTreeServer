import asyncio
import sys
import threading
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Добавляем корень backend в PYTHONPATH для alembic CLI
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import DATABASE_URL
from db.tables import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме (--sql)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запуск миграций через async engine."""
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме.
    
    Работает как из синхронного контекста (alembic CLI),
    так и из async-контекста (вызов из lifespan FastAPI).
    """
    try:
        asyncio.get_running_loop()
        # Уже внутри async-контекста — запускаем в отдельном потоке
        # со своим event loop'ом, т.к. asyncio.run() нельзя вызвать
        # из работающего цикла.
        exc: list[Exception] = []

        def _run():
            try:
                asyncio.run(run_async_migrations())
            except Exception as e:
                exc.append(e)

        t = threading.Thread(target=_run)
        t.start()
        t.join()
        if exc:
            raise exc[0]
    except RuntimeError:
        # Нет работающего event loop — стандартный запуск
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
