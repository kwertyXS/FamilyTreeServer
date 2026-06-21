import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .person_event import PersonEventTable


class EventTable(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str]
    date: Mapped[str | None]
    date_sort: Mapped[int | None]
    description: Mapped[str | None]
    place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"))

    place = relationship("PlaceTable", lazy="joined")
    persons = relationship("PersonTable", secondary=PersonEventTable.__table__, lazy="selectin")
