import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from alembic.config import Config
from alembic import command
from src.core.cors import setup_cors
from src.api import main_router
from src.db.database import engine
from src.services.htpasswd_manager import ensure_htpasswd


@asynccontextmanager
async def lifespan(app: FastAPI):
    # при старте — накатить миграции Alembic
    alembic_cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
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

app.include_router(main_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", reload=True)