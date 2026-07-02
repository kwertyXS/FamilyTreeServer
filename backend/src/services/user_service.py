from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import randbelow

from argon2 import PasswordHasher
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import UserDep
from src.core.config import MAIL_FROM
from src.db.tables import UserTable, ConfirmCodeTable
from src.email.email import smtp
from src.repositories.SQLAlchemyRepositories import (
    UserRepository,
    ConfirmCodeRepository,
)
from src.schemas.user import AuthSchemas, VerifyCodeSchema
from src.utils.user_functions import get_refresh_token, get_access_token, check_refresh_token

ph = PasswordHasher()

async def register_service(session, body: AuthSchemas):
    if await UserRepository(session).get_by_email(body.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = ph.hash(body.password)
    table = UserTable(email=body.email, password_hash=password_hash)
    await UserRepository(session).add(table)
    await session.commit()
    refresh_data = await get_refresh_token(session, table.id)
    access_token = await get_access_token(session, table.id)

    return {
        "status": "ok",
        "refresh_token": refresh_data["refresh_token"],
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

    refresh_data = await get_refresh_token(session, user.id)
    access_token = await get_access_token(session, user.id)

    return {
        "status": "ok",
        "refresh_token": refresh_data["refresh_token"],
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



async def accept_elua_service(session: AsyncSession, user_id):
    table = await UserRepository(session).get_by_id(user_id)
    if table is None:
        raise HTTPException(status_code=401, detail="Auth Error")
    table.elua = True
    await session.commit()
    return {
        "status": "ok"
    }


async def send_confirm_code_service(session: AsyncSession, user_id: str):
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Auth Error")

    code = f"{randbelow(1_000_000):06d}"
    code_hash = sha256(code.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # удаляем старые коды для этого email
    await ConfirmCodeRepository(session).delete_by_email(user.email)

    new_code = ConfirmCodeTable(email=user.email, code_hash=code_hash, expires_at=expires_at)
    await ConfirmCodeRepository(session).add(new_code)
    await session.commit()

    # отправляем письмо
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>Подтверждение email</h2>
    <p>Ваш код подтверждения:</p>
    <h1 style="letter-spacing: 6px; background: #f0f0f0; padding: 12px; text-align: center;">{code}</h1>
    <p>Код действует 10 минут.</p>
    <p>Если вы не запрашивали этот код — проигнорируйте письмо.</p>
</body>
</html>"""
    await smtp.connect()
    try:
        await smtp.send_html(
            to=user.email,
            subject="Код подтверждения",
            html=html,
            from_addr=MAIL_FROM,
        )
    finally:
        await smtp.close()

    return {"status": "ok"}


async def verify_confirm_code_service(session: AsyncSession, user_id: str, body: VerifyCodeSchema):
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Auth Error")

    code_hash = sha256(body.code.encode()).hexdigest()
    repo = ConfirmCodeRepository(session)
    record = await repo.get_by_email(user.email)

    if record is None:
        raise HTTPException(status_code=400, detail="Code not found or expired")

    if record.code_hash != code_hash:
        raise HTTPException(status_code=400, detail="Invalid code")

    if record.expires_at < datetime.utcnow():
        await session.delete(record)
        await session.commit()
        raise HTTPException(status_code=400, detail="Code expired")

    # код верный — удаляем запись и подтверждаем email
    await session.delete(record)
    user.email_confirm = True
    await session.commit()

    return {"status": "ok"}
