from abc import ABC, abstractmethod

from sqlalchemy import select, delete

from src.db.database import session_factory
from src.db.tables import Base


class AbstractRepository(ABC):
    @abstractmethod
    async def rewrite(self, data: list):
        raise NotImplementedError()

    @abstractmethod
    async def get_all(self):
        raise NotImplementedError()


class SQLAlchemyRepository(AbstractRepository):
    _model: Base = None

    async def rewrite(self, data: list):
        async with session_factory() as session:
            await session.execute(delete(self._model))
            await session.commit()
            session.add_all(data)
            await session.commit()

    async def get_all(self):
        async with session_factory() as session:
            stmt = select(self._model)
            res = await session.execute(stmt)
            return res.scalars().all()
