"""pytest configuration — FastAPI test client with in-memory SQLite."""

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.db.database import get_session
from tests.test_db import (
    init_test_db,
    drop_test_db,
    override_get_session,
    get_test_session,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# Test DB lifecycle — per-test to ensure isolation
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create all tables before each test, drop after. Isolated per test."""
    await init_test_db()
    yield
    await drop_test_db()


# ---------------------------------------------------------------------------
# FastAPI test client with overridden DB
# ---------------------------------------------------------------------------
@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with get_session overridden to in-memory SQLite."""
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Direct session access for test helpers
# ---------------------------------------------------------------------------
@pytest.fixture
async def db_session():
    """Provide a clean session for direct DB operations in tests."""
    async with get_test_session() as session:
        yield session
