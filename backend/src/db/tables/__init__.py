# Association tables (person_event, person_relation) должны быть импортированы
# раньше person и event, т.к. те используют .__table__ в secondary=.
from .base import Base
from .person_event import PersonEventTable
from .person_relation import PersonRelationTable
from .family import FamilyTable
from .place import PlaceTable
from .event import EventTable
from .person import PersonTable

__all__ = [
    "Base",
    "PersonTable",
    "PersonEventTable",
    "PersonRelationTable",
    "FamilyTable",
    "PlaceTable",
    "EventTable",
]
