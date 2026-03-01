"""Bridge revision for payments migration chain.

Revision ID: 568d2128ae73
Revises: c93e2c2314a7
Create Date: 2026-03-01 11:30:00.000000
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "568d2128ae73"
down_revision: Union[str, None] = "c93e2c2314a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op bridge migration."""


def downgrade() -> None:
    """No-op bridge migration."""
