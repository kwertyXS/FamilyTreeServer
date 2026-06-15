import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from alembic.config import Config
from alembic import command
from core.cors import setup_cors
from api import admin, family, test
from db.database import engine
from services.htpasswd_manager import ensure_htpasswd


@asynccontextmanager
async def lifespan(app: FastAPI):
    # при старте — накатить миграции Alembic
    alembic_cfg = Config(str(Path(__file__).parent / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    ensure_htpasswd()  # при старте — создать .htpasswd, если его нет
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