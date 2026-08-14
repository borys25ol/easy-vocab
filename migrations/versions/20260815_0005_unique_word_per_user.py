"""Make a word unique per user

Revision ID: 20260815_0005
Revises: 20260814_0004
Create Date: 2026-08-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260815_0005"
down_revision: str | None = "20260814_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()

    # Creation always lowercased, but updates did not until recently, so a
    # renamed row can sit here in mixed case. Normalise before adding the
    # constraint, or "Take Off" and "take off" would both be allowed and the
    # duplicate they represent would survive.
    connection.execute(sa.text("UPDATE words SET word = lower(word)"))

    # Refuse to guess which of a duplicated pair to keep. Deleting a user's
    # words to make a migration pass is worse than stopping and asking.
    duplicates = connection.execute(
        sa.text(
            "SELECT user_id, word, count(*) AS n FROM words "
            "GROUP BY user_id, word HAVING count(*) > 1"
        )
    ).fetchall()
    if duplicates:
        listed = ", ".join(f"user {row[0]}: {row[1]!r} x{row[2]}" for row in duplicates)
        raise RuntimeError(
            "words holds duplicates that the new constraint forbids. "
            f"Remove all but one of each, then run this again. Found: {listed}"
        )

    op.create_unique_constraint("uq_words_user_word", "words", ["user_id", "word"])


def downgrade() -> None:
    op.drop_constraint("uq_words_user_word", "words", type_="unique")
