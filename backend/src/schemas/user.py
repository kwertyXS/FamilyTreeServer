from pydantic import BaseModel, Field, EmailStr


class AuthSchemas(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4, max_length=25)


class RefreshSchema(BaseModel):
    refresh_token: str