"""Add token version for session revocation

Revision ID: 20260814_0003
Revises: 20260814_0002
Create Date: 2026-08-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260814_0003"
down_revision: str | None = "20260814_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # server_default fills the existing rows. Drop it afterwards so the
    # application stays the only writer of the version.
    op.add_column(
        "user",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("user", "token_version", server_default=None)


def downgrade() -> None:
    op.drop_column("user", "token_version")
