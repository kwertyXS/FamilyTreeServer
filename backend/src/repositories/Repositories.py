from abc import ABC, abstractmethod
from typing import AsyncGenerator

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import Base


class AbstractRepository(ABC):
    @abstractmethod
    async def rewrite(self, data: list):
        raise NotImplementedError()

    @abstractmethod
    async def get_all(self):
        raise NotImplementedError()


class SQLAlchemyRepository(AbstractRepository):
    def __init__(self, model: Base, session: AsyncSession):
        self._model = model
        self._session = session

    async def rewrite(self, data: list):
        async with self._session.begin():
            await self._session.execute(delete(self._model))
            # await self._session.flash()
            self._session.add_all(data)

    async def get_all(self):
        stmt = select(self._model)
        res = await self._session.execute(stmt)
        return res.scalars().all()
