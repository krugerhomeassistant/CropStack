"""The household's AI co-pilot settings."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: str | Sequence[str] | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("household", schema=None) as batch_op:
        batch_op.add_column(sa.Column("ai", sa.JSON(), server_default="{}", nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("household", schema=None) as batch_op:
        batch_op.drop_column("ai")
