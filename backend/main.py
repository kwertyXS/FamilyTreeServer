import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from core.cors import setup_cors
from api import admin, family, test
from db.database import engine
from db.models import Base
from services.htpasswd_manager import ensure_htpasswd


async def _migrate_sex_column():
    """Перенос sex с VARCHAR(1) на BOOLEAN для существующих БД."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'persons' AND column_name = 'sex'"
            )
        )
        row = result.fetchone()
        if row and row[0] in ("character varying", "text"):
            print("  ↻ Миграция sex: VARCHAR → BOOLEAN")
            await conn.execute(
                text(
                    "ALTER TABLE persons ALTER COLUMN sex TYPE BOOLEAN "
                    "USING CASE "
                    "  WHEN sex = 'М' THEN true "
                    "  WHEN sex = 'Ж' THEN false "
                    "  ELSE NULL END"
                )
            )
            print("  ✓ Миграция sex завершена")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # при старте — создать таблицы, если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # миграция sex VARCHAR → BOOLEAN
    await _migrate_sex_column()
    # при старте — создать .htpasswd, если его нет
    ensure_htpasswd()
    yield
    await engine.dispose()


app = FastAPI(
    title="FamilyTreeServer",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

setup_cors(app)

app.include_router(admin.router)
app.include_router(family.router)
app.include_router(test.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)