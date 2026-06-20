from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PersonRelationTable(Base):
    __tablename__ = "person_relations"
    __table_args__ = (
        UniqueConstraint("person_id", "related_person_id", name="uq_person_relations"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[str] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    related_person_id: Mapped[str] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    relation_type: Mapped[str]
    relation_label: Mapped[str]
