import uuid

from sqlalchemy.orm import mapped_column, Mapped

from src.db.tables import Base


class UserTable(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str]
    elua: Mapped[bool] = mapped_column(default=False)
    email_confirm: Mapped[bool] = mapped_column(default=False)
    can_invite: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)