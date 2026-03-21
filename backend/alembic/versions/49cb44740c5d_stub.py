"""Stub for missing revision 49cb44740c5d

Revision ID: 49cb44740c5d
Revises: 568d2128ae73
Create Date: 2026-03-05 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '49cb44740c5d'
down_revision: Union[str, None] = '568d2128ae73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
