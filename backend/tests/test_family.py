"""Tests for /api/tree, /api/persons, /api/persons/{id}, /api/events.

Each test gets a fresh in-memory DB (autouse setup_test_db in conftest).
"""

import pytest
from httpx import AsyncClient

from tests.test_db import get_test_session
from src.db.tables import (
    PlaceTable,
    FamilyTable,
    PersonTable,
    EventTable,
    PersonEventTable,
    PersonRelationTable,
)


async def _load_test_family_data():
    """Insert a minimal test dataset: 1 place, 1 family, 2 persons, 1 event.

    Inserted in FK-dependency order so SQLite doesn't hit FK constraint errors.
    """
    async with get_test_session() as session:
        place = PlaceTable(id="pl-1", full_name="Москва", name="Москва")
        family = FamilyTable(id="fam-1", name="Ивановы")
        session.add_all([place, family])
        await session.flush()

        person1 = PersonTable(
            id="p-1",
            full_name="Иван Иванов",
            sex=True,
            surname="Иванов",
            first_name="Иван",
            family_id="fam-1",
            birth_date="01.01.1980",
        )
        person2 = PersonTable(
            id="p-2",
            full_name="Мария Иванова",
            sex=False,
            surname="Иванова",
            first_name="Мария",
            family_id="fam-1",
            birth_date="15.05.1985",
        )
        session.add_all([person1, person2])
        await session.flush()

        event = EventTable(
            id="ev-1",
            type="Рождение",
            date="01.01.1980",
            date_sort=1980,
            place_id="pl-1",
            person_id="p-1",
        )
        session.add(event)
        await session.flush()

        pe = PersonEventTable(person_id="p-1", event_id="ev-1", role="Основной")
        rel = PersonRelationTable(
            person_id="p-1",
            related_person_id="p-2",
            relation_type="A",
            relation_label="Жена",
        )
        session.add_all([pe, rel])
        await session.commit()



@pytest.mark.anyio
async def test_tree_empty(client: AsyncClient):
    resp = await client.get("/api/tree")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"persons": [], "edges": []}


@pytest.mark.anyio
async def test_persons_empty(client: AsyncClient):
    resp = await client.get("/api/persons")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_person_not_found(client: AsyncClient):
    resp = await client.get("/api/persons/nonexistent")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Person not found"


@pytest.mark.anyio
async def test_events_empty(client: AsyncClient):
    resp = await client.get("/api/events")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_tree_with_data(client: AsyncClient):
    await _load_test_family_data()

    resp = await client.get("/api/tree")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["persons"]) == 2
    person_ids = {p["id"] for p in data["persons"]}
    assert person_ids == {"p-1", "p-2"}

    # 1 edge (spouse type A: person_id="p-1", related_person_id="p-2")
    assert len(data["edges"]) == 1
    edge = data["edges"][0]
    assert edge["from_id"] == "p-1"
    assert edge["to_id"] == "p-2"
    assert edge["type"] == "spouse"


@pytest.mark.anyio
async def test_persons_list(client: AsyncClient):
    await _load_test_family_data()

    resp = await client.get("/api/persons")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {p["full_name"] for p in data}
    assert names == {"Иван Иванов", "Мария Иванова"}


@pytest.mark.anyio
async def test_person_detail(client: AsyncClient):
    await _load_test_family_data()

    resp = await client.get("/api/persons/p-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "p-1"
    assert data["full_name"] == "Иван Иванов"
    assert data["sex"] is True
    assert data["family_name"] == "Ивановы"
    assert len(data["relations"]) == 1
    assert data["relations"][0]["related_person_id"] == "p-2"
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "Рождение"
    assert data["events"][0]["place"]["full_name"] == "Москва"


@pytest.mark.anyio
async def test_events_list(client: AsyncClient):
    await _load_test_family_data()

    resp = await client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    ev = data[0]
    assert ev["type"] == "Рождение"
    assert ev["date"] == "01.01.1980"
    assert ev["person"]["full_name"] == "Иван Иванов"
    assert ev["place"]["full_name"] == "Москва"
