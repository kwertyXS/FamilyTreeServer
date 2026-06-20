from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.db.database import session_factory
from src.db.tables import *
from src.repositories.Repositories import SQLAlchemyRepository


class EventRepository(SQLAlchemyRepository):
    _model = EventTable

    async def get_all(self):
        async with session_factory() as session:
            stmt = (
                select(self._model)
                .options(joinedload(EventTable.place))
                .order_by(EventTable.date_sort.nulls_last(), EventTable.id)
            )
            res = await session.execute(stmt)
            return res.unique().scalars().all()


class FamilyRepository(SQLAlchemyRepository):
    _model = FamilyTable


class PersonRepository(SQLAlchemyRepository):
    _model = PersonTable

    async def get_all(self):
        async with session_factory() as session:
            stmt = select(self._model).options(joinedload(PersonTable.family))
            res = await session.execute(stmt)
            return res.unique().scalars().all()

    async def get_by_id(self, person_id: str):
        async with session_factory() as session:
            stmt = (
                select(self._model)
                .options(
                    joinedload(PersonTable.family),
                    joinedload(PersonTable.birth_place),
                    joinedload(PersonTable.death_place),
                    joinedload(PersonTable.place_rel),
                    joinedload(PersonTable.events).joinedload(EventTable.place),
                )
                .where(PersonTable.id == person_id)
            )
            res = await session.execute(stmt)
            return res.unique().scalar_one_or_none()


class PersonEventRepository(SQLAlchemyRepository):
    _model = PersonEventTable


class PersonRelationRepository(SQLAlchemyRepository):
    _model = PersonRelationTable


class PlaceRepository(SQLAlchemyRepository):
    _model = PlaceTable
