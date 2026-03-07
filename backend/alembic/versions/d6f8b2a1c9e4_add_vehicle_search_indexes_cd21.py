"""Add vehicle search indexes for CD-21.

Revision ID: d6f8b2a1c9e4
Revises: c4d7a9e1f3b2
Create Date: 2026-03-03 14:35:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d6f8b2a1c9e4"
down_revision: Union[str, None] = "c4d7a9e1f3b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_vehicles_make;")
    op.execute("DROP INDEX IF EXISTS ix_vehicles_model;")
    op.execute("DROP INDEX IF EXISTS ix_vehicles_year;")
    op.execute("DROP INDEX IF EXISTS ix_vehicles_status;")

    op.execute("CREATE INDEX IF NOT EXISTS idx_make ON vehicles (make);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_model ON vehicles (model);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_year ON vehicles (year);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_price_jpy ON vehicles (price_jpy);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_status ON vehicles (status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_make_model ON vehicles (make, model);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_year_price ON vehicles (year, price_jpy);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_year_price;")
    op.execute("DROP INDEX IF EXISTS idx_make_model;")
    op.execute("DROP INDEX IF EXISTS idx_status;")
    op.execute("DROP INDEX IF EXISTS idx_price_jpy;")
    op.execute("DROP INDEX IF EXISTS idx_year;")
    op.execute("DROP INDEX IF EXISTS idx_model;")
    op.execute("DROP INDEX IF EXISTS idx_make;")

    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicles_make ON vehicles (make);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicles_model ON vehicles (model);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicles_year ON vehicles (year);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicles_status ON vehicles (status);")
