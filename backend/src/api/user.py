from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import UserDep
from src.db.database import get_session
from src.schemas.user import AuthSchemas, RefreshSchema, VerifyCodeSchema
from src.services.user_service import (
    register_service,
    login_service,
    refresh_service,
    accept_elua_service,
    send_confirm_code_service,
    verify_confirm_code_service,
)

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


@router.post("/send_code")
async def send_code(session: sessionDep, user_id: UserDep):
    return await send_confirm_code_service(session, user_id)


@router.post("/verify_code")
async def verify_code(body: VerifyCodeSchema, session: sessionDep, user_id: UserDep):
    return await verify_confirm_code_service(session, user_id, body)


