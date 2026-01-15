import datetime

from sqlmodel import Field, SQLModel


class Word(SQLModel, table=True):
    __tablename__ = "words"

    id: int | None = Field(default=None, primary_key=True, index=True)
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

    @classmethod
    def from_dict(cls, data: dict) -> "Word":
        data["word"] = data["word"].lower()
        return cls(**data)
