from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.db.database import session_factory
from src.db.tables import PersonTable, EventTable, PersonRelationTable, PersonEventTable
from src.schemas.family import *

router = APIRouter()


@router.get("/tree", response_model=TreeSchemaOut)
async def get_tree():
    """Полное дерево: все люди + связи для отрисовки на фронте."""

    async with session_factory() as session:
        persons = (await session.execute(
            select(PersonTable).options(joinedload(PersonTable.family))
        )).unique().scalars().all()

        relations = (await session.execute(
            select(PersonRelationTable)
        )).scalars().all()

    nodes = [
        TreeNodeSchemaOut(
            id=p.id,
            full_name=p.full_name,
            sex=p.sex,
            birth_date=p.birth_date,
            death_date=p.death_date,
            lifespan=p.lifespan,
            photo=p.photo,
            is_favorite=p.is_favorite,
            family_name=p.family.name if p.family else None,
        )
        for p in persons
    ]

    # Ребро — каждый parent-child как "parent", spouse как "spouse"
    REL_PARENT_CODES = {"F", "M", "S", "D"}
    REL_SPOUSE_CODES = {"A", "B"}
    REL_SIBLING_CODES = {"FS", "FD", "MS", "MD", "BS", "BD"}
    REL_EX_SPOUSE = {"L"}

    edges = []
    seen_edges = set()

    for r in relations:
        p1, p2, rtype, rlabel = r.person_id, r.related_person_id, r.relation_type, r.relation_label
        key = tuple(sorted((p1, p2))) + (rtype,)
        if key in seen_edges:
            continue
        seen_edges.add(key)

        if rtype in REL_PARENT_CODES:
            edge_type = "parent"
        elif rtype in REL_SPOUSE_CODES:
            edge_type = "spouse"
        elif rtype in REL_SIBLING_CODES:
            edge_type = "sibling"
        elif rtype in REL_EX_SPOUSE:
            edge_type = "ex_spouse"
        else:
            edge_type = "other"

        edges.append(TreeEdgeSchemaOut(from_id=p1, to_id=p2, type=edge_type))

    return TreeSchemaOut(persons=nodes, edges=edges)


@router.get("/persons/{person_id}", response_model=PersonSchemaOut)
async def get_person(person_id: str):
    """Детальная информация о персоне."""
    async with session_factory() as session:
        person = (await session.execute(
            select(PersonTable)
            .options(
                joinedload(PersonTable.family),
                joinedload(PersonTable.birth_place),
                joinedload(PersonTable.death_place),
                joinedload(PersonTable.place_rel),
                joinedload(PersonTable.events).joinedload(EventTable.place),
            )
            .where(PersonTable.id == person_id)
        )).unique().scalar_one_or_none()

        if person is None:
            raise HTTPException(404, "Person not found")

        relations = (await session.execute(
            select(PersonRelationTable).where(
                PersonRelationTable.person_id == person_id
            )
        )).scalars().all()

        person_events_participation = (await session.execute(
            select(PersonEventTable).where(
                PersonEventTable.person_id == person_id
            )
        )).scalars().all()

    # События с ролью
    event_roles = {pe.event_id: pe.role for pe in person_events_participation}

    events_out = []
    for ev in person.events:
        events_out.append(EventSchemaOut(
            id=ev.id,
            type=ev.type,
            date=ev.date,
            description=ev.description,
            place=PlaceSchema.from_orm(ev.place),
        ))

    return PersonSchemaOut(
        id=person.id,
        full_name=person.full_name,
        sex=person.sex,
        surname=person.surname,
        first_name=person.first_name,
        middle_name=person.middle_name,
        birth_date=person.birth_date,
        death_date=person.death_date,
        lifespan=person.lifespan,
        is_favorite=person.is_favorite,
        family_name=person.family.name if person.family else None,
        photo=person.photo,
        occupation=person.occupation,
        maiden_surname=person.maiden_surname,
        death_reason=person.death_reason,
        biography=person.biography,
        birth_place=PlaceSchema.from_orm(person.birth_place),
        death_place=PlaceSchema.from_orm(person.death_place),
        place=PlaceSchema.from_orm(person.place_rel),
        events=events_out,
        relations=[
            RelationSchemaOut(person_id=r.person_id, related_person_id=r.related_person_id, relation_label=r.relation_label)
            for r in relations
        ],
    )


@router.get("/events")
async def get_events():
    """Все события, отсортированные по году (хронология)."""
    async with session_factory() as session:
        events = (await session.execute(
            select(EventTable).options(joinedload(EventTable.place)).order_by(EventTable.date_sort.nulls_last(), EventTable.id)
        )).unique().scalars().all()

    return [
        {
            "id": e.id,
            "type": e.type,
            "date": e.date,
            "description": e.description,
            "place": PlaceSchema.from_orm(e.place).model_dump() if e.place else None,
        }
        for e in events
    ]
