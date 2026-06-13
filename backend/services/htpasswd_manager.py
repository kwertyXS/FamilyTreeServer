import os
import secrets
import string
import subprocess
import logging

HTPASSWD_PATH = os.getenv("HTPASSWD_PATH", "/app/auth/.htpasswd")
DEFAULT_USER = os.getenv("HTPASSWD_USER", "admin")

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

    # Если Docker создал директорию вместо файла (bind mount несуществующего пути)
    if os.path.isdir(HTPASSWD_PATH):
        os.rmdir(HTPASSWD_PATH)

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


def change_password(user: str, new_password: str) -> None:
    """Сменить пароль в .htpasswd."""
    entry = f"{user}:{_apr1_hash(new_password)}\n"
    os.makedirs(os.path.dirname(HTPASSWD_PATH), exist_ok=True)
    with open(HTPASSWD_PATH, "w") as f:
        f.write(entry)
    logger.info("Пароль для %s изменён", user)
