import os
import shutil
from io import BytesIO
from zipfile import ZipFile, BadZipFile

from fastapi import APIRouter, UploadFile, HTTPException
from services.xml_parser import parse_and_save

OUTPUT_PHOTOS = "/var/photos"

router = APIRouter(prefix="/api/admin")

@router.post("/load_xml_file")
async def load_xml_file(file: UploadFile):
    # --- проверка типа ---
    if file.content_type not in ("application/xml", "text/xml", ""):
        raise HTTPException(400, f"Ожидается XML, получен: {file.content_type}")

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Пустой файл")

    # --- парсинг и сохранение ---
    try:
        await parse_and_save(raw)
    except Exception as e:
        raise HTTPException(422, f"Ошибка парсинга XML: {e}")

    return {"status": "ok", "message": "Данные загружены"}


@router.post("/load_photos")
async def load_photos(file: UploadFile):
    if file.content_type not in ["application/zip", "application/x-zip-compressed"]:
        raise HTTPException(400, "Ожидается ZIP архив")

    data = await file.read()

    try:
        with ZipFile(BytesIO(data)) as zip_file:
            if os.path.exists(OUTPUT_PHOTOS):
                for entry in os.listdir(OUTPUT_PHOTOS):
                    entry_path = os.path.join(OUTPUT_PHOTOS, entry)
                    if os.path.isfile(entry_path):
                        os.remove(entry_path)
                    elif os.path.isdir(entry_path):
                        shutil.rmtree(entry_path)
            os.makedirs(OUTPUT_PHOTOS, exist_ok=True)

            zip_file.extractall(OUTPUT_PHOTOS)
            files = zip_file.namelist()

    except BadZipFile:
        raise HTTPException(400, "Файл не является корректным ZIP архивом")

    return {"status": "ok", "files": files}


@router.get("/test")
async def test():
    return {"status": "ok"}
