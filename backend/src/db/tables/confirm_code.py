import uuid
from datetime import datetime

from sqlalchemy.orm import mapped_column, Mapped

from src.db.tables import Base


class ConfirmCodeTable(Base):
    __tablename__ = "confirm_codes"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
