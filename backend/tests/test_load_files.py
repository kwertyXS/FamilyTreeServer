"""Tests for loading example XML/GEDCOM files and verifying DB content.

Creates reference snapshots on first run; compares against them on subsequent runs.
"""

import json
from pathlib import Path

import pytest
from httpx import AsyncClient

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
XML_FILE = Path(__file__).parent.parent / "exemple" / "test.xml"
GED_FILE = Path(__file__).parent.parent / "exemple" / "test.ged"


async def _fetch_api_snapshot(client: AsyncClient) -> dict:
    """Query all family API endpoints and return a snapshot dict."""
    tree = (await client.get("/api/tree")).json()
    persons = (await client.get("/api/persons")).json()
    events = (await client.get("/api/events")).json()
    return {"tree": tree, "persons": persons, "events": events}



@pytest.mark.anyio
async def test_xml_load_and_snapshot(client: AsyncClient):
    """Load test.xml and verify via reference snapshot.

    If no snapshot exists yet, creates one (run with --update-snapshots).
    Snapshot mismatch indicates the parser/API output changed.
    """
    xml_bytes = XML_FILE.read_bytes()
    assert xml_bytes, "test.xml is empty"

    resp = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("test.xml", xml_bytes, "application/xml")},
    )
    assert resp.status_code == 200, f"XML load failed: {resp.text}"
    assert resp.json() == {"status": "ok"}

    snapshot = await _fetch_api_snapshot(client)

    snapshot_path = SNAPSHOT_DIR / "xml_snapshot.json"

    tree = snapshot["tree"]
    assert len(tree["persons"]) > 0, "Tree should contain persons"
    assert len(tree["edges"]) > 0, "Tree should contain edges"

    persons_list = snapshot["persons"]
    assert len(persons_list) > 0, "Persons list should not be empty"

    events_list = snapshot["events"]
    assert len(events_list) > 0, "Events list should not be empty"

    _verify_pushkin_data(tree["persons"], persons_list, events_list)


def _verify_pushkin_data(tree_persons: list, persons_list: list, events_list: list):
    """Verify A.S. Pushkin's data is correctly loaded and exposed via API."""
    pushkin_tree = next((p for p in tree_persons if "Пушкин" in p.get("full_name", "") and "Александр Сергеевич" in p.get("full_name", "")), None)
    assert pushkin_tree is not None, "Pushkin not found in tree"
    assert pushkin_tree["is_favorite"] is True, "Pushkin should be favorite"
    assert pushkin_tree["full_name"] == "Пушкин Александр Сергеевич"
    assert pushkin_tree["family_name"] == "Пушкины"

    pushkin_p = next((p for p in persons_list if p.get("id") == pushkin_tree["id"]), None)
    assert pushkin_p is not None, "Pushkin not found in persons list"
    assert pushkin_p["full_name"] == "Пушкин Александр Сергеевич"

    pushkin_detail = next((p for p in tree_persons if p["id"] == pushkin_tree["id"]), None)
    assert pushkin_detail is not None
    assert pushkin_detail["lifespan"] == "37"
    assert pushkin_detail["sex"] is True  # М → True

    assert len(events_list) >= 1

    known_names = {"Пушкин Александр Сергеевич", "Пушкина (Гончарова) Наталья Николаевна",
                   "Ганнибал Абрам (Ибрагим) Петрович"}
    tree_names = {p["full_name"] for p in tree_persons}
    assert known_names.issubset(tree_names), f"Known persons missing: {known_names - tree_names}"


@pytest.mark.anyio
async def test_gedcom_load(client: AsyncClient):
    """Load test.ged and verify basic data integrity."""
    ged_bytes = GED_FILE.read_bytes()
    assert ged_bytes, "test.ged is empty"

    resp = await client.post(
        "/api/admin/load_gedcom",
        files={"file": ("test.ged", ged_bytes, "text/plain")},
    )
    assert resp.status_code == 200, f"GEDCOM load failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "ok"

    tree = (await client.get("/api/tree")).json()
    assert len(tree["persons"]) > 0, "No persons loaded from GEDCOM"
    assert len(tree["edges"]) > 0

    persons_list = (await client.get("/api/persons")).json()
    assert len(persons_list) > 0

    events = (await client.get("/api/events")).json()
    assert len(events) > 0

    pushkin = next(
        (p for p in tree["persons"]
         if "Александр" in p.get("full_name", "")
         and "Сергеевич" in p.get("full_name", "")
         and "Пушкин" in p.get("full_name", "")),
        None,
    )
    assert pushkin is not None, (
        f"Pushkin not found in GEDCOM-loaded tree. "
        f"Sample names: {[p['full_name'] for p in tree['persons'][:5]]}"
    )


@pytest.mark.anyio
async def test_xml_snapshot_regression(client: AsyncClient):
    """Verify XML data matches the stored reference snapshot."""
    xml_bytes = XML_FILE.read_bytes()
    resp = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("test.xml", xml_bytes, "application/xml")},
    )
    assert resp.status_code == 200

    snapshot = await _fetch_api_snapshot(client)
    snapshot_path = SNAPSHOT_DIR / "xml_snapshot.json"

    if not snapshot_path.exists():
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        pytest.skip("Snapshot created — re-run to verify")

    expected = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert snapshot == expected, (
        f"API output differs from snapshot {snapshot_path}\n"
        "If the change is intentional, delete the snapshot file and re-run to update."
    )


@pytest.mark.anyio
async def test_xml_reload_idempotent(client: AsyncClient):
    """Loading XML twice should produce the same output (rewrite is idempotent)."""
    xml_bytes = XML_FILE.read_bytes()

    resp1 = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("test.xml", xml_bytes, "application/xml")},
    )
    assert resp1.status_code == 200
    snap1 = await _fetch_api_snapshot(client)
    count1 = len(snap1["tree"]["persons"])

    resp2 = await client.post(
        "/api/admin/load_xml_file",
        files={"file": ("test.xml", xml_bytes, "application/xml")},
    )
    assert resp2.status_code == 200
    snap2 = await _fetch_api_snapshot(client)
    count2 = len(snap2["tree"]["persons"])

    assert count1 == count2, f"Person count changed after reload: {count1} → {count2}"
    assert snap1["tree"]["persons"] == snap2["tree"]["persons"], "Tree differs after reload"
