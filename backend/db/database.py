from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
