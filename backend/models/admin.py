from fastapi import UploadFile, HTTPException
from pydantic import BaseModel, Field, field_validator

MB = 8 * 1024 * 1024
GB = MB * 1024

class XMLFileModel(BaseModel):
    file: UploadFile

    @field_validator("file")
    def validate_file(cls, file: UploadFile):
        if file.content_type not in ("application/xml", "text/xml", ""):
            raise ValueError(f"Ожидается XML, получен: {file.content_type}")
        if file.size // MB <= 100:
            raise  ValueError(f"Вес файла больше 100 мегабайт")

        return file

class PhotosFileModel(BaseModel):
    file: UploadFile

    @field_validator("file")
    def validate_file(cls, file: UploadFile):
        if file.content_type not in ["application/zip", "application/x-zip-compressed"]:
            raise ValueError(f"Ожидается zip, получен: {file.content_type}")
        if file.size // GB <= 10:
            raise  ValueError(f"Вес файла больше 10 гигабайт")

        return file


class ChangeAccountModel(BaseModel):
    login: str | None = None
    password: str | None = None

    @field_validator("login", "password")
    @classmethod
    def validate_length(cls, v):
        if v is not None and (len(v) < 4 or len(v) > 35):
            raise ValueError("Длина поля должна быть от 4 до 35 символов")
        return v

    @field_validator("login")
    @classmethod
    def validate_login(cls, v):
        if v is not None and not v.isprintable():
            raise ValueError("Логин содержит недопустимые символы")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if v is not None and ":" in v:
            raise ValueError("Пароль не может содержать символ :")
        return v

