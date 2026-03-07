"""Add gallery_images to vehicles

Revision ID: d9a1f2b7c3e4
Revises: b2c3d4e5f6a7
Create Date: 2026-03-04 11:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9a1f2b7c3e4"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("gallery_images", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("vehicles", "gallery_images")
