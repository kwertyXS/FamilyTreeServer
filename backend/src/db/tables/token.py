import datetime
import uuid

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import mapped_column, Mapped

from src.db.tables import Base


class TokenTable(Base):
    __tablename__ = 'tokens'

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    refresh_token: Mapped[str]
    device_id: Mapped[str] = mapped_column(default=lambda: str(uuid.uuid4()), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.utcnow() + datetime.timedelta(days=30)
    )