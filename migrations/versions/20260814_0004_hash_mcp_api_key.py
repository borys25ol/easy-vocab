"""Store MCP API keys as hashes

Revision ID: 20260814_0004
Revises: 20260814_0003
Create Date: 2026-08-14 00:00:00.000000

"""

import hashlib
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260814_0004"
down_revision: str | None = "20260814_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("user", "mcp_api_key", new_column_name="mcp_api_key_hash")
    op.execute("ALTER INDEX ix_user_mcp_api_key RENAME TO ix_user_mcp_api_key_hash")

    # Hash the keys already issued so existing MCP clients keep working with
    # the key they hold. Done in Python to match hash_mcp_api_key exactly.
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            'SELECT id, mcp_api_key_hash FROM "user" WHERE mcp_api_key_hash IS NOT NULL'
        )
    ).fetchall()
    for row_id, plaintext_key in rows:
        connection.execute(
            sa.text('UPDATE "user" SET mcp_api_key_hash = :hashed WHERE id = :id'),
            {
                "hashed": hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest(),
                "id": row_id,
            },
        )


def downgrade() -> None:
    # The plaintext keys are gone for good, so drop the values rather than
    # leave hashes sitting in a column the old code reads as a key.
    op.execute('UPDATE "user" SET mcp_api_key_hash = NULL')
    op.execute("ALTER INDEX ix_user_mcp_api_key_hash RENAME TO ix_user_mcp_api_key")
    op.alter_column("user", "mcp_api_key_hash", new_column_name="mcp_api_key")
