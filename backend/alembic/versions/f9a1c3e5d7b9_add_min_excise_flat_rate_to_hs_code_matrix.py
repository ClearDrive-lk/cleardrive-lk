"""add min excise flat rate to hs code matrix

Revision ID: f9a1c3e5d7b9
Revises: ea78ccc57cfe
Create Date: 2026-03-20 18:40:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9a1c3e5d7b9"
down_revision: Union[str, Sequence[str], None] = "ea78ccc57cfe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hs_code_matrix",
        sa.Column(
            "min_excise_flat_rate_lkr",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column("hs_code_matrix", "min_excise_flat_rate_lkr", server_default=None)


def downgrade() -> None:
    op.drop_column("hs_code_matrix", "min_excise_flat_rate_lkr")
