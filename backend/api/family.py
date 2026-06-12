from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from db.database import async_session_factory
from db.models import Person, Event, Place, Family, person_relation_table, person_event_table

router = APIRouter(prefix="/api")


# --- Pydantic схемы ---

class PlaceOut(BaseModel):
    id: str
    full_name: str
    latitude: float | None = None
    longitude: float | None = None

    @classmethod
    def from_orm(cls, p: Place | None) -> "PlaceOut | None":
        if p is None:
            return None
        return cls(id=p.id, full_name=p.full_name, latitude=p.latitude, longitude=p.longitude)


class PersonBrief(BaseModel):
    id: str
    full_name: str
    sex: str | None = None
    surname: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    birth_date: str | None = None
    death_date: str | None = None
    lifespan: str | None = None
    photo: str | None = None
    is_favorite: bool = False
    family_name: str | None = None


class PersonDetail(PersonBrief):
    occupation: str | None = None
    maiden_surname: str | None = None
    death_reason: str | None = None
    biography: str | None = None
    birth_place: PlaceOut | None = None
    death_place: PlaceOut | None = None
    place: PlaceOut | None = None
    events: list["EventBrief"] = []
    relations: list["RelationOut"] = []


class RelationOut(BaseModel):
    person_id: str
    related_person_id: str
    relation_label: str


class EventBrief(BaseModel):
    id: str
    type: str
    date: str | None = None
    description: str | None = None
    place: PlaceOut | None = None


class TreeNode(BaseModel):
    """Узел дерева для фронтенда (минимально)."""
    id: str
    full_name: str
    sex: str | None
    birth_date: str | None
    death_date: str | None
    lifespan: str | None
    photo: str | None = None
    is_favorite: bool
    family_name: str | None


class TreeEdge(BaseModel):
    """Ребро графа для фронтенда."""
    from_id: str
    to_id: str
    type: str   # "parent", "spouse", "sibling", "ex_spouse"


class TreeOut(BaseModel):
    persons: list[TreeNode]
    edges: list[TreeEdge]


# --- Эндпоинты ---

@router.get("/tree", response_model=TreeOut)
async def get_tree():
    """Полное дерево: все люди + связи для отрисовки на фронте."""
    async with async_session_factory() as session:
        persons = (await session.execute(
            select(Person).options(joinedload(Person.family))
        )).unique().scalars().all()

        relations = (await session.execute(
            select(person_relation_table)
        )).all()

    nodes = [
        TreeNode(
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
        p1, p2, rtype, rlabel = r
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

        edges.append(TreeEdge(from_id=p1, to_id=p2, type=edge_type))

    return TreeOut(persons=nodes, edges=edges)


@router.get("/persons/{person_id}", response_model=PersonDetail)
async def get_person(person_id: str):
    """Детальная информация о персоне."""
    async with async_session_factory() as session:
        person = (await session.execute(
            select(Person)
            .options(
                joinedload(Person.family),
                joinedload(Person.birth_place),
                joinedload(Person.death_place),
                joinedload(Person.place_rel),
                joinedload(Person.events).joinedload(Event.place),
            )
            .where(Person.id == person_id)
        )).unique().scalar_one_or_none()

        if person is None:
            raise HTTPException(404, "Person not found")

        relations = (await session.execute(
            select(person_relation_table).where(
                person_relation_table.c.person_id == person_id
            )
        )).all()

        person_events_participation = (await session.execute(
            select(person_event_table).where(
                person_event_table.c.person_id == person_id
            )
        )).all()

    # События с ролью
    event_roles = {pe.event_id: pe.role for pe in person_events_participation}

    events_out = []
    for ev in person.events:
        events_out.append(EventBrief(
            id=ev.id,
            type=ev.type,
            date=ev.date,
            description=ev.description,
            place=PlaceOut.from_orm(ev.place),
        ))

    return PersonDetail(
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
        birth_place=PlaceOut.from_orm(person.birth_place),
        death_place=PlaceOut.from_orm(person.death_place),
        place=PlaceOut.from_orm(person.place_rel),
        events=events_out,
        relations=[
            RelationOut(person_id=r.person_id, related_person_id=r.related_person_id, relation_label=r.relation_label)
            for r in relations
        ],
    )


@router.get("/events")
async def get_events():
    """Все события, отсортированные по году (хронология)."""
    async with async_session_factory() as session:
        events = (await session.execute(
            select(Event).options(joinedload(Event.place)).order_by(Event.date_sort.nulls_last(), Event.id)
        )).unique().scalars().all()

    return [
        {
            "id": e.id,
            "type": e.type,
            "date": e.date,
            "description": e.description,
            "place": PlaceOut.from_orm(e.place).model_dump() if e.place else None,
        }
        for e in events
    ]
