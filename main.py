import datetime
import json
import os
import re
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.params import Query
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai.types import GenerateContentConfig
from sqlmodel import Field, Session, SQLModel, create_engine, select, true
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

PROMPT = """
You are an English lexicography and corpus linguistics expert.
I am learning English words and phrases. Provide usage examples, translations, and linguistic data.

### REFERENCE EXAMPLES FOR STABILITY:
- "House" (Word) → Level: A1, Rank: 150, Group: Core 500, Range: 1-500
- "Challenge" (Word) → Level: B1, Rank: 1200, Group: Core Plus, Range: 1001-2000
- "Inevitable" (Word) → Level: B2, Rank: 4500, Group: Active Extended, Range: 3001-5000
- "Pragmatic" (Word) → Level: C1, Rank: 8500, Group: Advanced, Range: 7001-10000
- "Take care" (Phrase) → Level: A1, Rank: 300, Group: Very Common, Range: 1-500
- "Once in a blue moon" (Phrase) → Level: C1, Rank: 12000, Group: Very Rare, Range: 10000+

### INSTRUCTIONS:
1. Provide "level" strictly as a single value (A1, A2, B1, B2, C1, or C2).
2. Provide "rank" as a realistic estimated frequency number. Be consistent with the Reference Examples above.
3. For "synonyms":
   - Return them as a LIST of strings.
   - For words: provide 3-5 single-word synonyms.
   - For phrases: provide 2-3 alternative phrases.
4. "translation": Ukrainian language, comma-separated if multiple.
5. "category": Choose from [Phrases, Verbs, Nouns, Adverbs, Adjectives, Idioms]. Use "General" if no match.

### FREQUENCY RULES:
- WORDS: 1–500 (Core 500), 501–1000 (Core 1000), 1001–2000 (Core Plus), 2001–3000 (Active Basic), 3001–5000 (Active Extended), 5001–7000 (Fluent Core), 7001–10000 (Advanced), 10001–15000 (Academic), 15001–25000 (Rare), 25000+ (Obscure).
- PHRASES: 1–500 (Very Common), 501–2000 (Common), 2001–5000 (Less Common), 5001–10000 (Rare), 10000+ (Very Rare).

### RESPONSE FORMAT (JSON only):
{
    "word": "",
    "level": "B2",
    "type": "word | phrase",
    "is_phrasal": true | false,  // Set true only for phrasal verbs like "take off", "get out".
    "is_idiom": true | false,  // Set true for figurative expressions like "break the ice", "piece of cake".
    "frequency": 1-10,
    "rank": 1234,
    "rank_range": "1001-2000",
    "frequency_group": "...",
    "translation": "",
    "category": "",
    "synonyms": ["syn1", "syn2", "syn3"],
    "meanings": [
        {
            "partOfSpeech": "",
            "definitions": [{"definition": "", "example": ""}]
        }
    ]
}

Input: "%s"
"""

sqlite_file_name = "words_app.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


class Word(SQLModel, table=True):  # type: ignore
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
        default_factory=datetime.datetime.utcnow
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # Startup logic: Runs before the app starts receiving requests
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def get_usage_examples(word: str) -> dict:
    client = genai.Client(api_key=GOOGLE_API_KEY)

    word = word.lower()

    config = GenerateContentConfig(temperature=0.1)

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=PROMPT % word, config=config
    )

    clean_json = re.sub(
        r"^```json\s*|```$", "", response.text.strip(), flags=re.MULTILINE
    )
    data = json.loads(clean_json)

    examples_list = []
    for meaning in data.get("meanings", []):
        pos = meaning.get("partOfSpeech", "")
        for definition in meaning.get("definitions", []):
            ex = definition.get("example")
            if ex:
                examples_list.append(f"({pos}) {ex}")

    unique_examples = list(dict.fromkeys(examples_list))

    synonyms_raw = data.get("synonyms", [])
    if isinstance(synonyms_raw, list) and synonyms_raw:
        synonyms = ", ".join(synonyms_raw)
    else:
        synonyms = "No synonyms found"

    return {
        "rank": int(data.get("rank", 0)),
        "rank_range": str(data.get("rank_range", "-")),
        "translation": data.get("translation", ""),
        "category": data.get("category", "General"),
        "level": data.get("level", "A1"),
        "type": data.get("type", "Unknown"),
        "frequency": int(data.get("frequency", 1)),
        "frequency_group": data.get("frequency_group", "Unknown"),
        "examples": (
            "\n".join(unique_examples)
            if unique_examples
            else "Examples not found"
        ),
        "is_phrasal": bool(data.get("is_phrasal", False)),
        "is_idiom": bool(data.get("is_idiom", False)),
        "synonyms": synonyms,
    }


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("quiz.html", {"request": request})


@app.get("/quiz_translate", response_class=HTMLResponse)
async def quiz_translate_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "quiz_translate.html", {"request": request}
    )


@app.get("/flashcards", response_class=HTMLResponse)
async def flashcards_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("flashcards.html", {"request": request})


@app.get("/phrasal", response_class=HTMLResponse)
async def phrasal_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "phrasal_verbs.html", {"request": request}
    )


@app.get("/idioms", response_class=HTMLResponse)
async def phrasal_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("idioms.html", {"request": request})


@app.get("/words", response_model=list[Word])
def get_words(session: Session = Depends(get_session)) -> list[Word]:
    statement = select(Word).order_by(Word.created_at.desc())  # type: ignore
    return session.exec(statement).all()


@app.post("/words", response_model=Word)
def create_word(
    word_text: str = Query(..., alias="word"),
    session: Session = Depends(get_session),
) -> Word:
    word_info = get_usage_examples(word=word_text)

    new_word = Word(
        word=word_text.lower(),
        translation=word_info["translation"],
        examples=word_info["examples"],
        synonyms=word_info["synonyms"],
        rank=word_info["rank"],
        rank_range=word_info["rank_range"],
        category=word_info["category"],
        level=word_info["level"],
        type=word_info["type"],
        frequency=word_info["frequency"],
        frequency_group=word_info["frequency_group"],
        is_phrasal=word_info["is_phrasal"],
        is_idiom=word_info["is_idiom"],
    )
    session.add(new_word)
    session.commit()
    session.refresh(new_word)
    return new_word


@app.get("/words/phrasal_roots")
def get_phrasal_roots(session: Session = Depends(get_session)) -> list[str]:
    """
    Extracts unique roots ONLY from words marked as is_phrasal.
    """
    statement = select(Word).where(Word.is_phrasal == true())
    phrasal_verbs = session.exec(statement).all()

    roots = set()
    for v in phrasal_verbs:
        parts = v.word.split()
        if parts:
            roots.add(parts[0].strip().capitalize())

    return sorted(list(roots))


@app.get("/words/phrasal/{root}", response_model=list[Word])
def get_phrasal_verbs(
    root: str, session: Session = Depends(get_session)
) -> list[Word]:
    """
    Fetches phrasal verbs by root and strict is_phrasal flag.
    """
    search_pattern = f"{root.lower()} %"
    statement = (
        select(Word)
        .where(Word.word.like(search_pattern))  # type: ignore
        .where(Word.is_phrasal == true())
    )
    return session.exec(statement).all()


@app.get("/words/idioms", response_model=list[Word])
def get_idioms(session: Session = Depends(get_session)) -> list[Word]:
    """
    Fetches all words marked as idioms.
    """
    statement = (
        select(Word)
        .where(Word.is_idiom == true())
        .order_by(Word.created_at.desc())  # type: ignore
    )
    return session.exec(statement).all()


@app.put("/words/{word_id}", response_model=Word)
def update_word(
    word_id: int,
    word: str,
    translation: str,
    category: str,
    session: Session = Depends(get_session),
) -> Word:
    db_word = session.get(Word, word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")

    db_word.word = word
    db_word.translation = translation
    db_word.category = category

    session.add(db_word)
    session.commit()
    session.refresh(db_word)
    return db_word


@app.delete("/words/{word_id}")
def delete_word(word_id: int, session: Session = Depends(get_session)) -> dict:
    db_word = session.get(Word, word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")
    session.delete(db_word)
    session.commit()
    return {"message": "Deleted successfully"}


@app.patch("/words/{word_id}/toggle_learned", response_model=Word)
def toggle_learned(
    word_id: int, session: Session = Depends(get_session)
) -> Word:
    db_word = session.get(Word, word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")
    db_word.is_learned = not db_word.is_learned
    session.add(db_word)
    session.commit()
    session.refresh(db_word)
    return db_word
