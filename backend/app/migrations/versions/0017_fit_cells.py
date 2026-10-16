"""beds get cells that fit them exactly

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-16

"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.engine import layout  # pure maths, no database: safe to import here

revision: str = "0017"
down_revision: str | Sequence[str] | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """A 2.5 m bed on 30 cm cells had a last cell hanging 20 cm over its edge. Move such beds to the size that fits
    exactly and map their plantings onto it (the same ground, as when the owner changes the cell size by hand)."""
    db = op.get_bind()
    for bed_id, width, length, old in db.execute(sa.text("SELECT id, width, length, cell_cm FROM bed")).all():
        new = layout.fit_cell(width, length)
        if layout.fits(width, length, old) or new == old:
            continue
        for pid, cells in db.execute(sa.text("SELECT id, cells FROM planting WHERE bed_id = :b"), {"b": bed_id}).all():
            mapped = layout.remap(json.loads(cells) if isinstance(cells, str) else cells, old, new)
            cols, rows = layout.grid(width, length, new)
            mapped = [c for c in mapped if c[0] < cols and c[1] < rows]  # the overhang was never part of the bed
            db.execute(sa.text("UPDATE planting SET cells = :c WHERE id = :i"), {"c": json.dumps(mapped), "i": pid})
        db.execute(sa.text("UPDATE bed SET cell_cm = :c WHERE id = :i"), {"c": new, "i": bed_id})


def downgrade() -> None:
    pass  # the old cell sizes are not kept; the new ones are still valid
