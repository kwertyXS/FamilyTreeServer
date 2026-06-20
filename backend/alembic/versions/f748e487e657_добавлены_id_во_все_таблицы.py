"""добавлены id во все таблицы

Revision ID: f748e487e657
Revises: 6d2b68b48507
Create Date: 2026-06-20 23:37:21.712850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f748e487e657'
down_revision: Union[str, None] = '6d2b68b48507'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── person_events ──────────────────────────────────────────────────
    op.execute("""
        ALTER TABLE person_events DROP CONSTRAINT person_events_pkey;
        ALTER TABLE person_events ADD COLUMN id INTEGER;
        CREATE SEQUENCE sq_person_events_id;
        UPDATE person_events SET id = nextval('sq_person_events_id');
        ALTER TABLE person_events ALTER COLUMN id SET NOT NULL;
        ALTER TABLE person_events ALTER COLUMN id SET DEFAULT nextval('sq_person_events_id');
        ALTER TABLE person_events ADD PRIMARY KEY (id);
        ALTER TABLE person_events ADD CONSTRAINT uq_person_events UNIQUE (person_id, event_id);
        ALTER SEQUENCE sq_person_events_id OWNED BY person_events.id;
    """)

    # ─── person_relations ───────────────────────────────────────────────
    op.execute("""
        ALTER TABLE person_relations DROP CONSTRAINT person_relations_pkey;
        ALTER TABLE person_relations ADD COLUMN id INTEGER;
        CREATE SEQUENCE sq_person_relations_id;
        UPDATE person_relations SET id = nextval('sq_person_relations_id');
        ALTER TABLE person_relations ALTER COLUMN id SET NOT NULL;
        ALTER TABLE person_relations ALTER COLUMN id SET DEFAULT nextval('sq_person_relations_id');
        ALTER TABLE person_relations ADD PRIMARY KEY (id);
        ALTER TABLE person_relations ADD CONSTRAINT uq_person_relations UNIQUE (person_id, related_person_id);
        ALTER SEQUENCE sq_person_relations_id OWNED BY person_relations.id;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE person_events DROP CONSTRAINT uq_person_events;
        ALTER TABLE person_events DROP CONSTRAINT person_events_pkey;
        ALTER TABLE person_events DROP COLUMN id;
        ALTER TABLE person_events ADD PRIMARY KEY (person_id, event_id);
        DROP SEQUENCE IF EXISTS sq_person_events_id;
    """)
    op.execute("""
        ALTER TABLE person_relations DROP CONSTRAINT uq_person_relations;
        ALTER TABLE person_relations DROP CONSTRAINT person_relations_pkey;
        ALTER TABLE person_relations DROP COLUMN id;
        ALTER TABLE person_relations ADD PRIMARY KEY (person_id, related_person_id);
        DROP SEQUENCE IF EXISTS sq_person_relations_id;
    """)
