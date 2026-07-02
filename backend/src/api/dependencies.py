from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.repositories.SQLAlchemyRepositories import UserRepository
from src.utils.user_functions import check_access_token

bearer = HTTPBearer()
authDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]


async def get_current_user(credentials: authDep) -> str:
    result = await check_access_token(credentials.credentials)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return result[0]


async def get_current_admin(credentials: authDep) -> str:
    result = await check_access_token(credentials.credentials)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not result[1]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return result[0]


async def get_verified_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> str:
    result = await check_access_token(credentials.credentials)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = result[0]
    status = await UserRepository(session).check_verification_status(user_id)
    if status is None:
        raise HTTPException(status_code=401, detail="User not found")

    elua, email_confirm = status
    if not elua:
        raise HTTPException(status_code=403, detail="EULA not accepted")
    if not email_confirm:
        raise HTTPException(status_code=403, detail="Email not confirmed")

    return user_id


async def get_verified_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> str:
    result = await check_access_token(credentials.credentials)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = result[0]
    is_admin = result[1]

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    status = await UserRepository(session).check_verification_status(user_id)
    if status is None:
        raise HTTPException(status_code=401, detail="User not found")

    elua, email_confirm = status
    if not elua:
        raise HTTPException(status_code=403, detail="EULA not accepted")
    if not email_confirm:
        raise HTTPException(status_code=403, detail="Email not confirmed")

    return user_id


UserDep = Annotated[str, Depends(get_current_user)]
AdminDep = Annotated[str, Depends(get_current_admin)]
UserVerifiedDep = Annotated[str, Depends(get_verified_user)]
AdminVerifiedDep = Annotated[str, Depends(get_verified_admin)]
