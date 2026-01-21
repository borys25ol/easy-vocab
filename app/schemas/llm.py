from typing import Any

from pydantic import BaseModel, Field, field_validator


ALLOWED_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
ALLOWED_TYPES = {"word", "phrase"}
ALLOWED_CATEGORIES = {
    "Phrases",
    "Verbs",
    "Nouns",
    "Adverbs",
    "Adjectives",
    "Idioms",
    "General",
}


class LlmDefinition(BaseModel):
    definition: str = Field(min_length=1)
    example: str | None = None


class LlmMeaning(BaseModel):
    partOfSpeech: str | None = None
    definitions: list[LlmDefinition] = Field(default_factory=list)


class LlmResponse(BaseModel):
    word: str = Field(min_length=1)
    level: str
    type: str
    is_phrasal: bool = False
    is_idiom: bool = False
    frequency: int = 1
    rank: int = 0
    rank_range: str = "-"
    frequency_group: str = "Unknown"
    translation: str = ""
    category: str = "General"
    synonyms: list[str] = Field(default_factory=list)
    meanings: list[LlmMeaning] = Field(default_factory=list)

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        level = value.strip().upper()
        if level not in ALLOWED_LEVELS:
            raise ValueError("Invalid CEFR level")
        return level

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_TYPES:
            raise ValueError("Invalid type")
        return normalized

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in ALLOWED_CATEGORIES:
            return "General"
        return normalized

    @field_validator("synonyms", mode="before")
    @classmethod
    def normalize_synonyms(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",")]
            return [item for item in items if item]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, value: int) -> int:
        if value < 1 or value > 10:
            raise ValueError("Frequency out of expected range")
        return value

    @field_validator("rank")
    @classmethod
    def validate_rank(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Rank must be positive")
        return value
