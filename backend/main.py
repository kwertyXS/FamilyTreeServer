import uvicorn
from fastapi import FastAPI
from core.cors import setup_cors
from api import admin #, places, chat, suggestions

app = FastAPI(
    title="Places API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

setup_cors(app)

app.include_router(admin.router)
# app.include_router(places.router)
# app.include_router(chat.router)
# app.include_router(suggestions.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)