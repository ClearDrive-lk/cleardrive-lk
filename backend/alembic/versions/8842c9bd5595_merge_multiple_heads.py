"""Merge multiple heads

Revision ID: 8842c9bd5595
Revises: 3b8c44dc50d6, b7c9fdad010d, e22d44f5a757, f17d2c9a5b0e
Create Date: 2026-03-13 17:12:13.348119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8842c9bd5595'
down_revision: Union[str, None] = ('3b8c44dc50d6', 'b7c9fdad010d', 'e22d44f5a757', 'f17d2c9a5b0e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
