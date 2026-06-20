import os
import secrets
import string
import subprocess
import logging

from fastapi import HTTPException

from src.core.config import HTPASSWD_PATH, DEFAULT_USER
from src.schemas.admin import ChangeAccountSchema

logger = logging.getLogger(__name__)


_APR1_ALPHABET = string.ascii_letters + string.digits + "./" # Символы для соли APR1

def hash_func(password: str, salt: str | None = None) -> str:
    """Сгенерировать APR1 (MD5) хэш Apache htpasswd через openssl."""
    if salt is None:
        salt = "".join(secrets.choice(_APR1_ALPHABET) for _ in range(8))
    result = subprocess.run(
        ["openssl", "passwd", "-apr1", "-salt", salt, password],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()





async def change_account_service(body: ChangeAccountSchema) -> None:
    """Сменить логин и/или пароль в .htpasswd."""
    if body.login is None and body.password is None:
        raise HTTPException(400, "Укажите login и/или password")

    login = body.login
    password = body.password

    with open(HTPASSWD_PATH, "r") as f:
        parts = f.read().strip().split(":", 1)
    current_user = parts[0]
    current_hash = parts[1]

    new_user = login if login is not None else current_user
    new_hash = hash_func(password) if password is not None else current_hash

    entry = f"{new_user}:{new_hash}\n"
    with open(HTPASSWD_PATH, "w") as f:
        f.write(entry)
    logger.info("Учётная запись обновлена: %s", new_user)
