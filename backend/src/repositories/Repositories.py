from abc import ABC, abstractmethod

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from src.db.tables import Base


class AbstractRepository(ABC):
    @abstractmethod
    async def rewrite(self, data: list):
        raise NotImplementedError()

    @abstractmethod
    async def get_all(self):
        raise NotImplementedError()

    @abstractmethod
    async def get_by_id(self, id: str):
        raise NotImplementedError()

    @abstractmethod
    async def add(self, obj: Base | dict):
        raise NotImplementedError()


class SQLAlchemyRepository(AbstractRepository):
    def __init__(self, model, session: AsyncSession):
        self._model = model
        self._session = session

    async def rewrite(self, data: list[Base]):
        await self._session.execute(delete(self._model))
        self._session.add_all(data)
        await self._session.flush()

    async def get_all(self):
        stmt = select(self._model)
        res = await self._session.execute(stmt)
        return res.scalars().all()

    async def get_by_id(self, id: str):
        stmt = select(self._model).where(self._model.id == id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def add(self, obj: Base | dict):
        if isinstance(obj, dict):
            obj = self._model(**obj)

        self._session.add(obj)
        await self._session.flush()
        return obj


