"""Initial schema

Revision ID: 20260121_0001
Revises:
Create Date: 2026-01-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260121_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("mcp_api_key", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_mcp_api_key",
        "user",
        ["mcp_api_key"],
        unique=True,
    )
    op.create_index(
        "ix_user_username",
        "user",
        ["username"],
        unique=True,
    )
    op.create_table(
        "words",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("word", sa.String(), nullable=False),
        sa.Column("translation", sa.String(), nullable=False),
        sa.Column("examples", sa.String(), nullable=True),
        sa.Column("synonyms", sa.String(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("rank_range", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False),
        sa.Column("frequency_group", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column(
            "is_phrasal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_idiom",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_learned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_words_id", "words", ["id"], unique=False)
    op.create_index("ix_words_user_id", "words", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_words_user_id", table_name="words")
    op.drop_index("ix_words_id", table_name="words")
    op.drop_table("words")
    op.drop_index("ix_user_username", table_name="user")
    op.drop_index("ix_user_mcp_api_key", table_name="user")
    op.drop_table("user")
