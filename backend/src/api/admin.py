from fastapi import APIRouter, HTTPException, UploadFile
from src.schemas.admin import ChangeAccountSchema
from src.services.admin_service import load_xml_service, load_photos_service, load_gedcom_service
from src.services.password_service import change_account_service

router = APIRouter(prefix="/admin")


@router.post("/load_xml_file")
async def load_xml_file(file: UploadFile):
    await load_xml_service(file)
    return {"status": "ok"}


@router.post("/load_gedcom")
async def load_gedcom(file: UploadFile):
    msg = await load_gedcom_service(file)
    return {"status": "ok", "message": msg}


@router.post("/load_photos")
async def load_photos(file: UploadFile):
    count = await load_photos_service(file)
    return {"status": "ok", "count_files": count}


@router.post("/change_account")
async def change_admin_account(body: ChangeAccountSchema):
    await change_account_service(body)
    return {"status": "ok"}


