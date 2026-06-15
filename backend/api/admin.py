from zipfile import BadZipFile
from fastapi import APIRouter, HTTPException, UploadFile
from schemas.admin import ChangeAccountSchema
from services.extract_photos import extract_photos
from services.xml_parser import parse_and_save
from services.htpasswd_manager import change_account

router = APIRouter(prefix="/api/admin")


@router.post("/load_xml_file")
async def load_xml_file(file: UploadFile):
    if file.content_type not in ("application/xml", "text/xml", ""):
        raise HTTPException(400, f"Ожидается XML, получен: {file.content_type}")

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Пустой файл")

    try:
        await parse_and_save(raw)
    except Exception as e:
        raise HTTPException(422, f"Ошибка парсинга XML: {e}")

    return {"status": "ok"}


@router.post("/load_photos")
async def load_photos(file: UploadFile):
    if file.content_type not in ["application/zip", "application/x-zip-compressed"]:
        raise HTTPException(400, f"Ожидается ZIP, получен: {file.content_type}")
    data = await file.read()
    try:
        count = extract_photos(data)
    except BadZipFile:
        raise HTTPException(400, "Файл не является корректным ZIP архивом")

    return {"status": "ok", "count": count}


@router.post("/change_account")
async def change_admin_account(body: ChangeAccountSchema):
    if body.login is None and body.password is None:
        raise HTTPException(400, "Укажите login и/или password")
    change_account(body.login, body.password)
    return {"status": "ok"}


@router.post("/change_password")
async def change_admin_password(body: ChangeAccountSchema):
    if body.password is None:
        raise HTTPException(400, "Укажите password")
    change_account(body.login, body.password)
    return {"status": "ok"}