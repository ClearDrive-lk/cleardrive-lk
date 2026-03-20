"""merge tax catalog and dedicated rule heads

Revision ID: ea78ccc57cfe
Revises: 7a1c2d3e4f50, 5d2a7c9e3f11
Create Date: 2026-03-20 11:32:20.261857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea78ccc57cfe'
down_revision: Union[str, None] = ('7a1c2d3e4f50', '5d2a7c9e3f11')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
