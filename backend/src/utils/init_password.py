import os
import secrets

from src.core.config import HTPASSWD_PATH, DEFAULT_USER
from src.services.password_service import hash_func, logger


def init_password() -> str | None:
    """Создать .htpasswd с паролем по умолчанию, если файла нет.
    Возвращает пароль, если был создан, иначе None."""
    if os.path.isfile(HTPASSWD_PATH):
        return None

    password = secrets.token_urlsafe(12)
    user = DEFAULT_USER
    entry = f"{user}:{hash_func(password)}\n"

    os.makedirs(os.path.dirname(HTPASSWD_PATH), exist_ok=True)
    with open(HTPASSWD_PATH, "w", encoding="UTF8") as f:
        f.write(entry)

    logger.warning(
        (
        f"🔐 .htpasswd создан: {HTPASSWD_PATH}\n"
        f"   Логин: {user}\n"
        f"   Пароль: {password}\n"
        "   ⚠️  Смените пароль после входа!"
        )
    )
    return password



if __name__ == "__main__":
    init_password()