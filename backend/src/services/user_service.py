from datetime import datetime, timezone

from argon2 import PasswordHasher
from fastapi import HTTPException

from src.db.tables import UserTable
from src.repositories.SQLAlchemyRepositories import UserRepository
from src.schemas.user import AuthSchemas
from src.utils.user_functions import get_refresh_token, get_access_token, check_refresh_token

ph = PasswordHasher()

async def register_service(session, body: AuthSchemas):
    if await UserRepository(session).get_by_email(body.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = ph.hash(body.password)
    table = UserTable(email=body.email, password_hash=password_hash)
    await UserRepository(session).add(table)
    await session.commit()
    refresh_token = await get_refresh_token(session, table.id)
    access_token = await get_access_token(session, table.id)

    return {
        "status": "ok",
        "refresh_token": refresh_token,
        "access_token": access_token,
    }


async def login_service(session, body: AuthSchemas):
    user = await UserRepository(session).get_by_email(body.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    try:
        ph.verify(user.password_hash, body.password)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    refresh_token = await get_refresh_token(session, user.id)
    access_token = await get_access_token(session, user.id)

    return {
        "status": "ok",
        "refresh_token": refresh_token,
        "access_token": access_token,
    }


async def refresh_service(session, refresh_token: str):
    result = await check_refresh_token(session, refresh_token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id, device_id, expires_at = result
    if expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    access_token = await get_access_token(session, user_id)
    return {
        "status": "ok",
        "access_token": access_token,
    }


