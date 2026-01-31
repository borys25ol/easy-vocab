import datetime
from typing import TYPE_CHECKING, Any

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models.user import User
    from app.schemas.word import WordInfo


class Word(SQLModel, table=True):
    __tablename__ = "words"

    id: int | None = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    word: str = Field(nullable=False)
    translation: str = Field(nullable=False)
    examples: str | None = Field(default=None)
    synonyms: str | None = Field(default=None)
    rank: int = Field(nullable=False)
    rank_range: str = Field(nullable=False)
    level: str = Field(nullable=False)
    frequency: int = Field(nullable=False)
    frequency_group: str = Field(nullable=False)
    category: str = Field(nullable=False)
    type: str = Field(nullable=False)
    is_phrasal: bool = Field(default=False)
    is_idiom: bool = Field(default=False)
    is_learned: bool = Field(default=False)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )

    user: "User" = Relationship(back_populates="words")

    @classmethod
    def from_dict(cls, data: "WordInfo", user_id: int) -> "Word":
        clean_data = data.model_dump()
        clean_data["word"] = clean_data["word"].lower()
        return cls(**clean_data, user_id=user_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "word": self.word,
            "translation": self.translation,
            "examples": self.examples,
            "synonyms": self.synonyms,
            "rank": self.rank,
            "rank_range": self.rank_range,
            "level": self.level,
            "frequency": self.frequency,
            "frequency_group": self.frequency_group,
            "category": self.category,
            "type": self.type,
            "is_phrasal": self.is_phrasal,
            "is_idiom": self.is_idiom,
            "is_learned": self.is_learned,
            "created_at": self.created_at,
        }
