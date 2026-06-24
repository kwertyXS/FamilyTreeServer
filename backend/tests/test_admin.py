"""Tests for /api/admin/* endpoints."""

import pytest
from httpx import AsyncClient


# Minimal valid XML fixture
MINIMAL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<tree>
  <places/>
  <families/>
  <persons/>
  <events/>
</tree>"""


@pytest.mark.anyio
async def test_load_minimal_xml_success(client: AsyncClient):
    """Valid XML upload returns 200."""
    resp = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("test.xml", MINIMAL_XML.encode("utf-8"), "application/xml")},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_load_xml_wrong_content_type(client: AsyncClient):
    """Non-XML content type returns 400."""
    resp = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("test.txt", b"not xml", "text/plain")},
    )
    assert resp.status_code == 400
    assert "XML" in resp.json()["detail"]


@pytest.mark.anyio
async def test_load_xml_empty_file(client: AsyncClient):
    """Empty file returns 400."""
    resp = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("empty.xml", b"", "application/xml")},
    )
    assert resp.status_code == 400
    assert "Пустой файл" in resp.json()["detail"]


@pytest.mark.anyio
async def test_load_xml_invalid_xml(client: AsyncClient):
    """Malformed XML returns 422."""
    resp = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("bad.xml", b"<tree><broken>", "application/xml")},
    )
    assert resp.status_code == 422
    assert "Ошибка парсинга XML" in resp.json()["detail"]


@pytest.mark.anyio
async def test_load_gedcom_empty_file(client: AsyncClient):
    """Empty GEDCOM file returns 400."""
    resp = await client.post(
        "/api/admin/load_gedcom",
        files={"file": ("empty.ged", b"", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Пустой файл" in resp.json()["detail"]


@pytest.mark.anyio
async def test_load_gedcom_invalid_encoding(client: AsyncClient):
    """Non-UTF-8 file returns 422."""
    resp = await client.post(
        "/api/admin/load_gedcom",
        files={"file": ("bad.ged", b"\xff\xfe\x00\x01", "text/plain")},
    )
    assert resp.status_code == 422
    assert "кодировке UTF-8" in resp.json()["detail"]


@pytest.mark.anyio
async def test_load_photos_not_zip(client: AsyncClient):
    """Non-ZIP file returns 400."""
    resp = await client.post(
        "/api/admin/load_photos",
        files={"file": ("photo.jpg", b"not a zip", "image/jpeg")},
    )
    assert resp.status_code == 400
    assert "ZIP" in resp.json()["detail"]
