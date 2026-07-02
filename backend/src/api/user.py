from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import UserDep
from src.db.database import get_session
from src.schemas.user import AuthSchemas, RefreshSchema
from src.services.user_service import register_service, login_service, refresh_service, accept_elua_service

router = APIRouter(prefix="/auth")

sessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/register")
async def register(body: AuthSchemas, session: sessionDep):
    return await register_service(session, body)


@router.post("/login")
async def login(body: AuthSchemas, session: sessionDep):
    return await login_service(session, body)


@router.post("/refresh")
async def refresh(body: RefreshSchema, session: sessionDep):
    return await refresh_service(session, body.refresh_token)



@router.post("/accept_elua")
async def accept_elua(session: sessionDep, user_id: UserDep):
    return await accept_elua_service(session, user_id)


