"""Tests for /api/health endpoint."""

import pytest


@pytest.mark.anyio
async def test_health(client):
    """GET /api/health returns 200 with status ok."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"status": "ok"}
