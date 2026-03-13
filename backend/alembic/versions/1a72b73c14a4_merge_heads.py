"""merge heads

Revision ID: 1a72b73c14a4
Revises: 49cb44740c5d, cd92_expand_audit
Create Date: 2026-03-10 19:50:20.654771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a72b73c14a4'
down_revision: Union[str, None] = ('49cb44740c5d', 'cd92_expand_audit')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
