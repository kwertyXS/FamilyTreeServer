from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PlaceTable(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    name: Mapped[str | None]
    short_name: Mapped[str | None]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"))

    parent = relationship("PlaceTable", remote_side=[id], lazy="joined")
