from fastapi import APIRouter, UploadFile
from models.admin import *
# from services.geocode_service import geocode_address
from db.session import engine, session


router = APIRouter(prefix="/api/admin")

@router.post("/load_file")
async def load_file(file: UploadFile):
    data = await file.read()
    return {"status": "ok",
            "text": data}


@router.get("/test")
async def load_file():
    return {"status": "ok"}
