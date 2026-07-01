from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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


UserDep = Annotated[str, Depends(get_current_user)]
AdminDep = Annotated[str, Depends(get_current_admin)]
