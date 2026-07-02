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


# ---------------------------------------------------------------------------
# Authenticated user fixture — registers a test user, accepts EULA + confirms email
# ---------------------------------------------------------------------------
@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a test user, verify EULA + email, return auth headers."""
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200

    # Grant EULA acceptance + email confirmation directly in DB
    async with get_test_session() as session:
        from src.repositories.SQLAlchemyRepositories import UserRepository
        user = await UserRepository(session).get_by_email("test@example.com")
        assert user is not None
        user.elua = True
        user.email_confirm = True
        await session.commit()

    # Get a fresh token (login reads up-to-date DB state)
    resp = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Admin auth fixture — registers a user, grants admin + verifications
# ---------------------------------------------------------------------------
@pytest.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    """Register a user, make them admin, verify EULA + email, return auth headers."""
    # Register
    resp = await client.post("/api/auth/register", json={
        "email": "admin@example.com",
        "password": "adminpass123",
    })
    assert resp.status_code == 200

    # Grant admin + verifications directly in DB
    async with get_test_session() as session:
        from src.repositories.SQLAlchemyRepositories import UserRepository
        user = await UserRepository(session).get_by_email("admin@example.com")
        assert user is not None
        user.is_admin = True
        user.elua = True
        user.email_confirm = True
        await session.commit()

    # Get a fresh token (login reads is_admin from DB)
    resp = await client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpass123",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
