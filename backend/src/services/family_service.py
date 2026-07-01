from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import PersonRelationTable, PersonEventTable
from src.repositories.SQLAlchemyRepositories import PersonRelationRepository, PersonRepository, EventRepository
from src.schemas.family import TreeEdgeSchemaOut, TreeSchemaOut, TreeNodeSchemaOut, PersonSchemaOut, EventSchemaOut, \
    PlaceSchema, RelationSchemaOut, PersonSchema, PersonBriefSchema
from src.utils.user_functions import check_access_token


async def get_tree_service(session: AsyncSession, token: str) -> TreeSchemaOut:
    if await check_access_token(token) is None:
        raise HTTPException(401, "Token is invalid")

    persons = await PersonRepository(session).get_all()
    relations = await PersonRelationRepository(session).get_all()

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

    for r in relations:
        p1, p2, rtype, rlabel = r.person_id, r.related_person_id, r.relation_type, r.relation_label

        if rtype in REL_PARENT_CODES:
            # Только прямое направление — от родителя к ребёнку (F, M)
            # S (сын) / D (дочь) — обратное, пропускаем
            if rtype not in {"F", "M"}:
                continue
            # В БД person_id = ребёнок, related_person_id = родитель — разворачиваем
            p1, p2 = p2, p1
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



async def get_person_service(session: AsyncSession, person_id: str) -> PersonSchemaOut:
    person = await PersonRepository(session).get_by_id(person_id)
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



async def get_events_service(session: AsyncSession) -> list[EventSchemaOut]:
    events = await EventRepository(session).get_all()

    return [
        {
            "id": e.id,
            "type": e.type,
            "person": PersonBriefSchema(id=e.person.id, full_name=e.person.full_name).model_dump()
            if e.person else None,
            "date": e.date,
            "description": e.description,
            "place": PlaceSchema.from_orm(e.place).model_dump() if e.place else None,
        }
        for e in events
    ]


async def get_persons_service(session: AsyncSession) -> list[PersonSchema]:
    persons = await PersonRepository(session).get_all()
    return [
        PersonSchema(
            id=p.id,
            full_name=p.full_name,
            sex=p.sex,
            surname=p.surname,
            first_name=p.first_name,
            middle_name=p.middle_name,
            birth_date=p.birth_date,
            death_date=p.death_date,
            lifespan=p.lifespan,
            photo=p.photo,
            is_favorite=p.is_favorite,
            family_name=p.family.name if p.family else None,
        )
        for p in persons
    ]
