from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models.word import Word


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    mcp_api_key: str | None = Field(default=None, index=True, unique=True)

    words: list["Word"] = Relationship(back_populates="user")
