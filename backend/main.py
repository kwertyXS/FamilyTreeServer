import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.cors import setup_cors
from api import admin, family  #, places, chat, suggestions
from db.database import engine
from db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # при старте — создать таблицы, если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Places API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

setup_cors(app)

app.include_router(admin.router)
app.include_router(family.router)
# app.include_router(chat.router)
# app.include_router(suggestions.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)