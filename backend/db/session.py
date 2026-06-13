from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import DATABASE_URL


engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,
)

session = Session(
    engine,
    expire_on_commit=False,
    future=True,
)