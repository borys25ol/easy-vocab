from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, true

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.word import Word
from app.services.genai_service import get_usage_examples


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=Sequence[Word])
def get_words(session: Session = Depends(get_session)) -> Sequence[Word]:
    statement = select(Word).order_by(Word.created_at.desc())  # type: ignore
    return session.exec(statement).all()


@router.post("", response_model=Word)
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


@router.get("/phrasal_roots")
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

    return sorted(roots)


@router.get("/phrasal/{root}", response_model=Sequence[Word])
def get_phrasal_verbs(
    root: str, session: Session = Depends(get_session)
) -> Sequence[Word]:
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


@router.get("/idioms", response_model=Sequence[Word])
def get_idioms(session: Session = Depends(get_session)) -> Sequence[Word]:
    """
    Fetches all words marked as idioms.
    """
    statement = (
        select(Word).where(Word.is_idiom == true()).order_by(Word.created_at.desc())  # type: ignore
    )
    return session.exec(statement).all()


@router.put("/{word_id}", response_model=Word)
def update_word(
    word_id: int,
    word: str,
    translation: str,
    category: str,
    session: Session = Depends(get_session),
) -> Word:
    db_word = session.get(entity=Word, ident=word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")

    db_word.word = word
    db_word.translation = translation
    db_word.category = category

    session.add(db_word)
    session.commit()
    session.refresh(db_word)
    return db_word


@router.delete("/{word_id}")
def delete_word(
    word_id: int, session: Session = Depends(get_session)
) -> dict[str, str]:
    db_word = session.get(entity=Word, ident=word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")
    session.delete(db_word)
    session.commit()
    return {"message": "Deleted successfully"}


@router.patch("/{word_id}/toggle_learned", response_model=Word)
def toggle_learned(word_id: int, session: Session = Depends(get_session)) -> Word:
    db_word = session.get(entity=Word, ident=word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")
    db_word.is_learned = not db_word.is_learned
    session.add(db_word)
    session.commit()
    session.refresh(db_word)
    return db_word
