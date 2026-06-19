from src.db.tables import *
from src.utils.repository import SQLAlchemyRepository


class EventRepository(SQLAlchemyRepository):
    _model = EventTable


class FamilyRepository(SQLAlchemyRepository):
    _model = FamilyTable


class PersonRepository(SQLAlchemyRepository):
    _model = PersonTable


class PersonEventRepository(SQLAlchemyRepository):
    _model = PersonEventTable


class PersonRelationRepository(SQLAlchemyRepository):
    _model = PersonRelationTable


class PlaceRepository(SQLAlchemyRepository):
    _model = PlaceTable
