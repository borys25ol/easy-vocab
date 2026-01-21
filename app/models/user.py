from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models.word import Word


class User(SQLModel, table=True):  # type:ignore
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

    words: list["Word"] = Relationship(back_populates="user")
