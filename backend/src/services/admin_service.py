import os
import shutil
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile, HTTPException

from src.core.config import OUTPUT_PHOTOS
from src.utils.xml_parser import XMLParser
from src.utils.gedcom_parser import GedcomParser


async def load_xml_service(file: UploadFile):
    if file.content_type not in ("application/xml", "text/xml", ""):
        raise HTTPException(400, f"Ожидается XML, получен: {file.content_type}")

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Пустой файл")

    try:
        await XMLParser().parse_and_save(raw)
    except Exception as e:
        raise HTTPException(422, f"Ошибка парсинга XML: {e}")


async def load_gedcom_service(file: UploadFile):
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Пустой файл")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(422, "Файл должен быть в кодировке UTF-8")

    try:
        msg = await GedcomParser().parse_and_save(text)
        return msg
    except Exception as e:
        raise HTTPException(422, f"Ошибка парсинга GEDCOM: {e}")



async def load_photos_service(file: UploadFile):
    if file.content_type not in ["application/zip", "application/x-zip-compressed"]:
        raise HTTPException(400, f"Ожидается ZIP, получен: {file.content_type}")
    data = await file.read()
    try:
        res = await extract_photos(data)
        return res
    except BadZipFile:
        raise HTTPException(400, "Файл не является корректным ZIP архивом")





async def extract_photos(data: bytes) -> int:
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
        return len(list(list(Path(OUTPUT_PHOTOS).rglob("*"))[0].rglob("*")))


