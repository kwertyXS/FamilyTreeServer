from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.db.tables import (
    EventTable,
    FamilyTable,
    PersonTable,
    PersonEventTable,
    PersonRelationTable,
    PlaceTable,
)
from src.repositories.Repositories import SQLAlchemyRepository


class EventRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(EventTable, session)

    async def get_all(self):
        stmt = (
            select(EventTable)
            .options(joinedload(EventTable.place))
            .order_by(EventTable.date_sort.nulls_last(), EventTable.id)
        )
        res = await self._session.execute(stmt)
        return res.unique().scalars().all()


class FamilyRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(FamilyTable, session)


class PersonRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(PersonTable, session)

    async def get_all(self):
        stmt = select(PersonTable).options(joinedload(PersonTable.family))
        res = await self._session.execute(stmt)
        return res.unique().scalars().all()

    async def get_by_id(self, person_id: str):
        stmt = (
            select(PersonTable)
            .options(
                joinedload(PersonTable.family),
                joinedload(PersonTable.birth_place),
                joinedload(PersonTable.death_place),
                joinedload(PersonTable.place_rel),
                joinedload(PersonTable.events).joinedload(EventTable.place),
            )
            .where(PersonTable.id == person_id)
        )
        res = await self._session.execute(stmt)
        return res.unique().scalar_one_or_none()


class PersonEventRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(PersonEventTable, session)


class PersonRelationRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(PersonRelationTable, session)


class PlaceRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(PlaceTable, session)
