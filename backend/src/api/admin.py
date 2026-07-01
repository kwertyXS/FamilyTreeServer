from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import UserDep, AdminDep
from src.db.database import get_session
from src.schemas.admin import ChangeAccountSchema
from src.services.admin_service import load_xml_service, load_photos_service, load_gedcom_service
from src.services.password_service import change_account_service

router = APIRouter(prefix="/admin")

sessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/load_xml_file")
async def load_xml_file(session: sessionDep, user_id: AdminDep, file: UploadFile):
    await load_xml_service(session, file)
    return {"status": "ok"}


@router.post("/load_gedcom")
async def load_gedcom(session: sessionDep, user_id: AdminDep, file: UploadFile):
    msg = await load_gedcom_service(session, file)
    return {"status": "ok", "message": msg}


@router.post("/load_photos")
async def load_photos(user_id: AdminDep, file: UploadFile):
    count = await load_photos_service(file)
    return {"status": "ok", "count_files": count}


@router.post("/change_account")
async def change_admin_account(user_id: AdminDep, body: ChangeAccountSchema):
    await change_account_service(body)
    return {"status": "ok"}


