from sqlalchemy import (
    Column, String, Text, Boolean, Float, Integer,
    ForeignKey, DateTime, Table, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PersonEventTable(Base):
    __tablename__ = "person_events"
    person_id: Mapped[str] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str]


class PersonRelationTable(Base):
    __tablename__ = "person_relations"
    person_id: Mapped[str] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    related_person_id: Mapped[str] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    relation_type: Mapped[str]
    relation_label: Mapped[str]


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


class EventTable(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[str]
    date: Mapped[str | None]
    date_sort: Mapped[int | None]
    description: Mapped[str | None]
    place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"))

    place = relationship("PlaceTable", lazy="joined")
    persons = relationship("PersonTable", secondary=PersonEventTable.__table__, lazy="selectin")


class FamilyTable(Base):
    __tablename__ = "families"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    male_surname: Mapped[str | None]
    female_surname: Mapped[str | None]