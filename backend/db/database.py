from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import DATABASE_URL


engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)

session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

