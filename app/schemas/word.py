import datetime
from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


# The text goes straight into an LLM prompt, so an unbounded value is billed
# to us. The longest thing worth storing is a phrase or an idiom, and 100
# characters covers that with room to spare. Surrounding whitespace is
# stripped before the length is checked, so a blank string is rejected.
WordText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]

# No minimum here. These are edited in a form, and clearing a field is a
# reasonable thing to do; only the length needs a ceiling.
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class WordCreate(BaseModel):
    word: WordText


class WordUpdate(BaseModel):
    word: WordText | None = None
    translation: ShortText | None = None
    category: ShortText | None = None


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


class WordListResponse(BaseModel):
    items: Sequence[WordRead]
    total: int
    limit: int | None
    offset: int
