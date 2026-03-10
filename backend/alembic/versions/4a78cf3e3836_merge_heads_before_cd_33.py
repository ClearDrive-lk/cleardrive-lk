"""Merge heads before CD-33

Revision ID: 4a78cf3e3836
Revises: 49cb44740c5d, cd92_expand_audit
Create Date: 2026-03-10 14:44:36.170576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a78cf3e3836'
down_revision: Union[str, None] = ('49cb44740c5d', 'cd92_expand_audit')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
