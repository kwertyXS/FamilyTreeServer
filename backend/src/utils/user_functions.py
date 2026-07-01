import hashlib
import secrets
from datetime import timedelta, datetime, timezone

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import SECRET_KEY, ALGORITHM
from src.db.tables import TokenTable
from src.repositories.SQLAlchemyRepositories import TokenRepository, UserRepository


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


async def get_refresh_token(session: AsyncSession, user_id: str):
    refresh_token = secrets.token_urlsafe(64)
    hash_refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    table = TokenTable(user_id=user_id, refresh_token=hash_refresh_token)
    await TokenRepository(session).add(table)
    await session.commit()
    return {
        "refresh_token": refresh_token,
        "device_id": table.device_id,
        "expires_at": table.expires_at
    }


async def check_refresh_token(session: AsyncSession, token):
    hash_refresh_token = hashlib.sha256(token.encode()).hexdigest()
    data = await TokenRepository(session).get_by_token(hash_refresh_token)
    if data is None:
        return None
    return data.user_id, data.device_id, data.expires_at



async def get_access_token(session, user_id: str):
    now = _utc_now()
    is_admin = await UserRepository(session).check_admin_privileges(user_id)
    payload = {
        "is_admin": bool(is_admin),
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def check_access_token(token: str) -> tuple[str, bool] | None:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if data["exp"] < int(_utc_now().timestamp()):
            return None
        return data["sub"], data["is_admin"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None