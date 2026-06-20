from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FamilyTable(Base):
    __tablename__ = "families"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    male_surname: Mapped[str | None]
    female_surname: Mapped[str | None]
