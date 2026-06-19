import os
import shutil
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from src.core.config import OUTPUT_PHOTOS


def extract_photos(data: bytes) -> int:
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
        return len(list(Path(OUTPUT_PHOTOS).rglob("*.*")))