from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .person_event import PersonEventTable
from .person_relation import PersonRelationTable


class PersonTable(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(primary_key=True)
    sex: Mapped[bool | None]
    surname: Mapped[str | None]
    maiden_surname: Mapped[str | None]
    first_name: Mapped[str | None]
    middle_name: Mapped[str | None]
    full_name: Mapped[str]
    occupation: Mapped[str | None]
    birth_date: Mapped[str | None]
    death_date: Mapped[str | None]
    death_reason: Mapped[str | None]
    lifespan: Mapped[str | None]
    is_favorite: Mapped[bool] = mapped_column(default=False)
    biography: Mapped[str | None]
    photo: Mapped[str | None]
    birth_place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"))
    death_place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"))
    place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"))
    family_id: Mapped[str | None] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"))

    birth_place = relationship("PlaceTable", foreign_keys=[birth_place_id], lazy="joined")
    death_place = relationship("PlaceTable", foreign_keys=[death_place_id], lazy="joined")
    place_rel = relationship("PlaceTable", foreign_keys=[place_id], lazy="joined")
    family = relationship("FamilyTable", lazy="joined")
    events = relationship("EventTable", secondary=PersonEventTable.__table__, lazy="selectin")
    relations = relationship(
        "PersonTable",
        secondary=PersonRelationTable.__table__,
        primaryjoin=id == PersonRelationTable.__table__.c.person_id,
        secondaryjoin=id == PersonRelationTable.__table__.c.related_person_id,
        lazy="selectin",
        viewonly=True,
    )
