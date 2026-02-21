"""Fix multiple heads

Revision ID: d20979ec042d
Revises: 13e4f8c8fc37, 568d2128ae73
Create Date: 2026-02-21 15:19:21.920447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd20979ec042d'
down_revision: Union[str, None] = ('13e4f8c8fc37', '568d2128ae73')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
