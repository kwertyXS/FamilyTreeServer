from fastapi import UploadFile, HTTPException
from pydantic import BaseModel, Field, field_validator


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

