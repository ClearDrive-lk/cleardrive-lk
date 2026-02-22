"""add audit_logs table

Revision ID: 611ce2705ddc
Revises: 3247b739293f
Create Date: 2026-02-22 07:20:40.606208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '611ce2705ddc'
down_revision: Union[str, None] = '3247b739293f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
