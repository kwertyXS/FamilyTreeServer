from zipfile import BadZipFile
from fastapi import APIRouter, HTTPException
from models.admin import XMLFileModel, PhotosFileModel, ChangeAccountModel
from services.extract_photos import extract_photos
from services.xml_parser import parse_and_save
from services.htpasswd_manager import change_account


router = APIRouter(prefix="/api/admin")


@router.post("/load_xml_file")
async def load_xml_file(body: XMLFileModel):
    raw = await body.file.read()
    if not raw:
        raise HTTPException(400, "Пустой файл")

    try:
        await parse_and_save(raw)
    except Exception as e:
        raise HTTPException(422, f"Ошибка парсинга XML: {e}")

    return {"status": "ok"}


@router.post("/load_photos")
async def load_photos(body: PhotosFileModel):
    data = await body.file.read()

    try:
        extract_photos(data)
    except BadZipFile:
        raise HTTPException(400, "Файл не является корректным ZIP архивом")

    return {"status": "ok"}


@router.post("/change_account")
async def change_admin_account(body: ChangeAccountModel):
    if body.login is None and body.password is None:
        raise HTTPException(400, "Укажите login и/или password")
    change_account(body.login, body.password)
    return {"status": "ok"}


@router.post("/change_password")
async def change_admin_password(body: ChangeAccountModel):
    if body.password is None:
        raise HTTPException(400, "Укажите password")
    change_account(body.login, body.password)
    return {"status": "ok"}