"""Merge remaining Alembic heads after shipping, finance, and email branches.

Revision ID: 6c4f0b2d9a1e
Revises: 3b8c44dc50d6, b7c9fdad010d, e22d44f5a757, f17d2c9a5b0e
Create Date: 2026-03-16 05:20:00.000000
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "6c4f0b2d9a1e"
down_revision: Union[str, Sequence[str], None] = (
    "3b8c44dc50d6",
    "b7c9fdad010d",
    "e22d44f5a757",
    "f17d2c9a5b0e",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
