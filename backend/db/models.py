import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Boolean, Float, Integer,
    ForeignKey, DateTime, Table, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# --- association tables ---

person_event_table = Table(
    "person_events",
    Base.metadata,
    Column("person_id", String, ForeignKey("persons.id"), primary_key=True),
    Column("event_id", String, ForeignKey("events.id"), primary_key=True),
    Column("role", String, nullable=False),
)

person_relation_table = Table(
    "person_relations",
    Base.metadata,
    Column("person_id", String, ForeignKey("persons.id"), primary_key=True),
    Column("related_person_id", String, ForeignKey("persons.id"), primary_key=True),
    Column("relation_type", String, nullable=False),       # relcode: F, M, B, A, S, D, FS, FD, ...
    Column("relation_label", String, nullable=False),      # human-readable: Отец, Мать, Жена, Сын...
)


class Person(Base):
    __tablename__ = "persons"

    id = Column(String, primary_key=True)                     # XML id (число, но храним строкой)
    sex = Column(String(1), nullable=True)
    surname = Column(String, nullable=True)                   # sn
    maiden_surname = Column(String, nullable=True)            # msn (девичья фамилия)
    first_name = Column(String, nullable=True)                # fn
    middle_name = Column(String, nullable=True)               # mn
    full_name = Column(String, nullable=False)
    occupation = Column(String, nullable=True)                # occu
    birth_date = Column(String, nullable=True)                # bdate (сырая строка из XML)
    death_date = Column(String, nullable=True)                # ddate
    death_reason = Column(String, nullable=True)              # dreason
    lifespan = Column(String, nullable=True)
    is_favorite = Column(Boolean, default=False)              # fav
    biography = Column(Text, nullable=True)                   # comment
    photo = Column(String, nullable=True)                     # путь к фото (из <document path="...">)
    birth_place_id = Column(String, ForeignKey("places.id"), nullable=True)
    death_place_id = Column(String, ForeignKey("places.id"), nullable=True)
    place_id = Column(String, ForeignKey("places.id"), nullable=True)  # основное место
    family_id = Column(String, ForeignKey("families.id"), nullable=True)

    birth_place = relationship("Place", foreign_keys=[birth_place_id], lazy="joined")
    death_place = relationship("Place", foreign_keys=[death_place_id], lazy="joined")
    place_rel = relationship("Place", foreign_keys=[place_id], lazy="joined")
    family = relationship("Family", lazy="joined")
    events = relationship("Event", secondary=person_event_table, lazy="selectin")
    relations = relationship(
        "Person",
        secondary=person_relation_table,
        primaryjoin=id == person_relation_table.c.person_id,
        secondaryjoin=id == person_relation_table.c.related_person_id,
        lazy="selectin",
        viewonly=True,
    )


class Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    name = Column(String, nullable=True)
    short_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    parent_id = Column(String, ForeignKey("places.id"), nullable=True)

    parent = relationship("Place", remote_side=[id], lazy="joined")


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)                     # Рождение, Свадьба, Смерть, etc.
    date = Column(String, nullable=True)                      # сырая строка даты
    date_sort = Column(Integer, nullable=True)                # год для сортировки
    description = Column(Text, nullable=True)                 # comment
    place_id = Column(String, ForeignKey("places.id"), nullable=True)

    place = relationship("Place", lazy="joined")
    persons = relationship("Person", secondary=person_event_table, lazy="selectin")


class Family(Base):
    __tablename__ = "families"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    male_surname = Column(String, nullable=True)              # ms
    female_surname = Column(String, nullable=True)            # fs
