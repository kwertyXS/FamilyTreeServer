import os
import secrets
import string
import subprocess
import logging

from src.core.config import HTPASSWD_PATH, DEFAULT_USER

logger = logging.getLogger(__name__)

# Символы для соли APR1
_APR1_ALPHABET = string.ascii_letters + string.digits + "./"


def _apr1_hash(password: str, salt: str | None = None) -> str:
    """Сгенерировать APR1 (MD5) хэш Apache htpasswd через openssl."""
    if salt is None:
        salt = "".join(secrets.choice(_APR1_ALPHABET) for _ in range(8))
    result = subprocess.run(
        ["openssl", "passwd", "-apr1", "-salt", salt, password],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def ensure_htpasswd() -> str | None:
    """Создать .htpasswd с паролем по умолчанию, если файла нет.
    Возвращает пароль, если был создан, иначе None."""
    if os.path.isfile(HTPASSWD_PATH):
        return None

    password = secrets.token_urlsafe(12)
    user = DEFAULT_USER
    entry = f"{user}:{_apr1_hash(password)}\n"

    os.makedirs(os.path.dirname(HTPASSWD_PATH), exist_ok=True)
    with open(HTPASSWD_PATH, "w", encoding="UTF8") as f:
        f.write(entry)

    logger.warning(
        "🔐 .htpasswd создан: %s\n"
        "   Логин: %s\n"
        "   Пароль: %s\n"
        "   ⚠️  Смените пароль после входа!",
        HTPASSWD_PATH, user, password,
    )
    return password


def change_account(login: str | None, password: str | None) -> None:
    """Сменить логин и/или пароль в .htpasswd."""
    with open(HTPASSWD_PATH, "r") as f:
        parts = f.read().strip().split(":", 1)
    current_user = parts[0]
    current_hash = parts[1]

    new_user = login if login is not None else current_user
    new_hash = _apr1_hash(password) if password is not None else current_hash

    entry = f"{new_user}:{new_hash}\n"
    with open(HTPASSWD_PATH, "w") as f:
        f.write(entry)
    logger.info("Учётная запись обновлена: %s", new_user)
