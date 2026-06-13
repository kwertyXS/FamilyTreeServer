from pydantic import BaseModel
from db.models import Place


class PlaceOut(BaseModel):
    id: str
    full_name: str
    latitude: float | None = None
    longitude: float | None = None

    @classmethod
    def from_orm(cls, p: Place | None) -> "PlaceOut | None":
        if p is None:
            return None
        return cls(id=p.id, full_name=p.full_name, latitude=p.latitude, longitude=p.longitude)


class PersonBrief(BaseModel):
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


class PersonDetail(PersonBrief):
    occupation: str | None = None
    maiden_surname: str | None = None
    death_reason: str | None = None
    biography: str | None = None
    birth_place: PlaceOut | None = None
    death_place: PlaceOut | None = None
    place: PlaceOut | None = None
    events: list["EventBrief"] = []
    relations: list["RelationOut"] = []


class RelationOut(BaseModel):
    person_id: str
    related_person_id: str
    relation_label: str


class EventBrief(BaseModel):
    id: str
    type: str
    date: str | None = None
    description: str | None = None
    place: PlaceOut | None = None


class TreeNode(BaseModel):
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


class TreeEdge(BaseModel):
    """Ребро графа для фронтенда."""
    from_id: str
    to_id: str
    type: str   # "parent", "spouse", "sibling", "ex_spouse"


class TreeOut(BaseModel):
    persons: list[TreeNode]
    edges: list[TreeEdge]