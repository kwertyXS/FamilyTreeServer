from pydantic import BaseModel

class LoginIn(BaseModel):
    password: str# = Field(le=25)


class LoginOut(BaseModel):
    status: bool = True
    token: str | None = None
