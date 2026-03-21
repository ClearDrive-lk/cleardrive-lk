"""merge all heads for deploy

Revision ID: cccb8e5e9fd0
Revises: 49cb44740c5d, 8842c9bd5595, b9e2279cf357
Create Date: 2026-03-18 09:29:20.667109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cccb8e5e9fd0'
down_revision: Union[str, None] = ('49cb44740c5d', '8842c9bd5595', 'b9e2279cf357')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
