from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.db.tables import *
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

class UserRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(UserTable, session)

    async def get_by_email(self, email: str) -> UserTable | None:
        stmt = select(UserTable).where(UserTable.email == email)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def check_admin_privileges(self, user_id: str) -> bool | None:
        stmt = select(UserTable.is_admin).where(UserTable.id == user_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def check_invite_privileges(self, user_id: str) -> bool | None:
        stmt = select(UserTable.can_invite).where(UserTable.id == user_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

class TokenRepository(SQLAlchemyRepository):
    def __init__(self, session):
        super().__init__(TokenTable, session)

    async def get_by_token(self, token: str):
        stmt = select(TokenTable).where(TokenTable.refresh_token == token)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()