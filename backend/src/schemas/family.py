from pydantic import BaseModel
from src.db.tables import PlaceTable


class PlaceSchema(BaseModel):
    id: str
    full_name: str
    latitude: float | None = None
    longitude: float | None = None

    @classmethod
    def from_orm(cls, p: PlaceTable | None) -> "PlaceSchema | None":
        if p is None:
            return None
        return cls(id=p.id, full_name=p.full_name, latitude=p.latitude, longitude=p.longitude)


class PersonSchema(BaseModel):
    id: str
    full_name: str
    sex: bool | None = None
    surname: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    birth_date: str | None = None
    death_date: str | None = None
    lifespan: str | None = None
    photo: str | None = None
    is_favorite: bool = False
    family_name: str | None = None


class PersonSchemaOut(PersonSchema):
    occupation: str | None = None
    maiden_surname: str | None = None
    death_reason: str | None = None
    biography: str | None = None
    birth_place: PlaceSchema | None = None
    death_place: PlaceSchema | None = None
    place: PlaceSchema | None = None
    events: list["EventSchemaOut"] = []
    relations: list["RelationSchemaOut"] = []


class RelationSchemaOut(BaseModel):
    person_id: str
    related_person_id: str
    relation_label: str


class EventSchemaOut(BaseModel):
    id: str
    type: str
    date: str | None = None
    description: str | None = None
    place: PlaceSchema | None = None


class TreeNodeSchemaOut(BaseModel):
    """Узел дерева для фронтенда (минимально)."""
    id: str
    full_name: str
    sex: bool | None
    birth_date: str | None
    death_date: str | None
    lifespan: str | None
    photo: str | None = None
    is_favorite: bool
    family_name: str | None


class TreeEdgeSchemaOut(BaseModel):
    """Ребро графа для фронтенда."""
    from_id: str
    to_id: str
    type: str   # "parent", "spouse", "sibling", "ex_spouse"


class TreeSchemaOut(BaseModel):
    persons: list[TreeNodeSchemaOut]
    edges: list[TreeEdgeSchemaOut]