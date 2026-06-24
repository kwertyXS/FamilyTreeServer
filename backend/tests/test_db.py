"""In-memory SQLite test database for pytest.

Usage:
  - override_get_session: drop-in replacement for src.db.database.get_session
  - init_test_db() / drop_test_db(): lifecycle helpers called from conftest
  - get_test_session(): context manager for direct DB access in test helpers

Uses SQLite's shared in-memory mode (file::memory:?cache=shared + uri=True)
so all connections from the same engine share one database.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
)

from src.db.tables import Base

# ---------------------------------------------------------------------------
# Engine — shared in-memory: all connections see the same database.
# ?uri=true instructs SQLAlchemy to pass uri=True to the aiosqlite/sqlite3 driver.
# ---------------------------------------------------------------------------
_test_engine = create_async_engine(
    "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true",
    echo=False,
    connect_args={"check_same_thread": False},
)


@event.listens_for(_test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    """Enable foreign-key enforcement (off by default in SQLite)."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Table lifecycle (called from conftest fixtures)
# ---------------------------------------------------------------------------
async def init_test_db() -> None:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_test_db() -> None:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override for FastAPI — replaces src.db.database.get_session."""
    async with _test_session_factory() as session:
        yield session


@asynccontextmanager
async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for direct session access in test helpers."""
    async with _test_session_factory() as session:
        yield session
