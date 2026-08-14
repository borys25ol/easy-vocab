"""Add login throttling columns

Revision ID: 20260814_0002
Revises: 20260121_0001
Create Date: 2026-08-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260814_0002"
down_revision: str | None = "20260121_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # server_default fills the existing rows. Drop it afterwards so the
    # application stays the only writer of the counter.
    op.add_column(
        "user",
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column("user", "failed_login_count", server_default=None)
    op.add_column(
        "user",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user", "locked_until")
    op.drop_column("user", "failed_login_count")
