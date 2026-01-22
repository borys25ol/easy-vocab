import datetime

from pydantic import BaseModel, ConfigDict


class WordBase(BaseModel):
    word: str
    translation: str | None = None
    category: str | None = None


class WordCreate(BaseModel):
    word: str


class WordUpdate(BaseModel):
    word: str | None = None
    translation: str | None = None
    category: str | None = None


class WordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    word: str
    translation: str
    examples: str | None
    synonyms: str | None
    rank: int
    rank_range: str
    level: str
    frequency: int
    frequency_group: str
    category: str
    type: str
    is_phrasal: bool
    is_idiom: bool
    is_learned: bool
    created_at: datetime.datetime


class WordInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    word: str
    rank: int
    rank_range: str
    translation: str
    category: str
    level: str
    type: str
    frequency: int
    frequency_group: str
    examples: str | None
    is_phrasal: bool
    is_idiom: bool
    synonyms: str | None
