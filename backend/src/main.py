import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api import main_router
from src.db.database import engine


app = FastAPI(
    title="FamilyTreeServer",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)



app.include_router(main_router)


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)