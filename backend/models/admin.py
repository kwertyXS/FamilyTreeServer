from fastapi import UploadFile
from pydantic import BaseModel

class LoadFile(BaseModel):
    file: UploadFile
    photos: UploadFile
