"""initial

Revision ID: c82931831974
Revises:
Create Date: 2026-06-13 23:14:57.818313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c82931831974"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "families",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("male_surname", sa.String(), nullable=True),
        sa.Column("female_surname", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "places",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("short_name", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("parent_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["places.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("date", sa.String(), nullable=True),
        sa.Column("date_sort", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("place_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["place_id"], ["places.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "persons",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("sex", sa.Boolean(), nullable=True),
        sa.Column("surname", sa.String(), nullable=True),
        sa.Column("maiden_surname", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("middle_name", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("occupation", sa.String(), nullable=True),
        sa.Column("birth_date", sa.String(), nullable=True),
        sa.Column("death_date", sa.String(), nullable=True),
        sa.Column("death_reason", sa.String(), nullable=True),
        sa.Column("lifespan", sa.String(), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("photo", sa.String(), nullable=True),
        sa.Column("birth_place_id", sa.String(), nullable=True),
        sa.Column("death_place_id", sa.String(), nullable=True),
        sa.Column("place_id", sa.String(), nullable=True),
        sa.Column("family_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["birth_place_id"], ["places.id"]),
        sa.ForeignKeyConstraint(["death_place_id"], ["places.id"]),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"]),
        sa.ForeignKeyConstraint(["place_id"], ["places.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "person_events",
        sa.Column("person_id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("person_id", "event_id"),
    )
    op.create_table(
        "person_relations",
        sa.Column("person_id", sa.String(), nullable=False),
        sa.Column("related_person_id", sa.String(), nullable=False),
        sa.Column("relation_type", sa.String(), nullable=False),
        sa.Column("relation_label", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["related_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("person_id", "related_person_id"),
    )


def downgrade() -> None:
    op.drop_table("person_relations")
    op.drop_table("person_events")
    op.drop_table("persons")
    op.drop_table("events")
    op.drop_table("places")
    op.drop_table("families")
