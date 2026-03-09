"""Add user_provided_data to kyc_documents

Revision ID: 8b7c1d2e3f4a
Revises: 03ff73db6c3c
Create Date: 2026-03-09 09:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b7c1d2e3f4a"
down_revision: Union[str, None] = "03ff73db6c3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kyc_documents", sa.Column("user_provided_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("kyc_documents", "user_provided_data")
