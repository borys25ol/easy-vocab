from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models.word import Word


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    mcp_api_key: str | None = Field(default=None, index=True, unique=True)

    # Bumped on logout. Tokens carry the value they were issued with, so
    # raising it here rejects every token handed out earlier. Without it a
    # captured token stays usable for the whole expiry window despite logout.
    token_version: int = Field(default=0)

    # Login throttling. The counter lives in the database rather than in
    # process memory because the deployment runs several replicas, and a
    # per-process counter would give an attacker one allowance per pod.
    failed_login_count: int = Field(default=0)
    locked_until: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    words: list["Word"] = Relationship(back_populates="user")

    def is_locked(self, now: datetime | None = None) -> bool:
        """Report whether the lock window is still open.

        SQLite drops the timezone, so a value read back from it is naive.
        Treat such a value as UTC to keep the comparison from raising.
        """
        if self.locked_until is None:
            return False

        locked_until = self.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=UTC)

        return locked_until > (now or datetime.now(UTC))
