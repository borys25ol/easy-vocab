from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, true

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.models.word import Word
from app.schemas.word import WordCreate, WordRead, WordUpdate
from app.services.genai_service import get_usage_examples


router = APIRouter(dependencies=[Depends(get_current_user)])


def get_user_word(word_id: int, user_id: int, session: Session) -> Word:
    """Helper to get a word that belongs to the specified user."""
    db_word = session.get(entity=Word, ident=word_id)
    if not db_word or db_word.user_id != user_id:
        raise HTTPException(status_code=404, detail="Word not found")
    return db_word


@router.get("", response_model=Sequence[WordRead])
def get_words(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Sequence[Word]:
    statement = (
        select(Word)
        .where(Word.user_id == current_user.id)
        .order_by(Word.created_at.desc())  # type: ignore
    )
    return session.exec(statement).all()


@router.post("", response_model=WordRead)
def create_word(
    word_in: WordCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Word:
    word_text = word_in.word
    word_info = get_usage_examples(word=word_text)

    new_word = Word(
        user_id=current_user.id,  # pyright: ignore[reportArgumentType]
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
def get_phrasal_roots(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """
    Extracts unique roots ONLY from words marked as is_phrasal for current user.
    """
    statement = (
        select(Word)
        .where(Word.user_id == current_user.id)
        .where(Word.is_phrasal == true())
    )
    phrasal_verbs = session.exec(statement).all()

    roots = set()
    for v in phrasal_verbs:
        parts = v.word.split()
        if parts:
            roots.add(parts[0].strip().capitalize())

    return sorted(roots)


@router.get("/phrasal/{root}", response_model=Sequence[WordRead])
def get_phrasal_verbs(
    root: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Sequence[Word]:
    """
    Fetches phrasal verbs by root and strict is_phrasal flag for current user.
    """
    search_pattern = f"{root.lower()} %"
    statement = (
        select(Word)
        .where(Word.user_id == current_user.id)
        .where(Word.word.like(search_pattern))  # type: ignore
        .where(Word.is_phrasal == true())
    )
    return session.exec(statement).all()


@router.get("/idioms", response_model=Sequence[WordRead])
def get_idioms(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Sequence[Word]:
    """
    Fetches all words marked as idioms for current user.
    """
    statement = (
        select(Word)
        .where(Word.user_id == current_user.id)
        .where(Word.is_idiom == true())
        .order_by(Word.created_at.desc())  # type: ignore
    )
    return session.exec(statement).all()


@router.put("/{word_id}", response_model=WordRead)
def update_word(
    word_id: int,
    word_update: WordUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Word:
    db_word = get_user_word(word_id, current_user.id, session)  # type: ignore

    if word_update.word is not None:
        db_word.word = word_update.word
    if word_update.translation is not None:
        db_word.translation = word_update.translation
    if word_update.category is not None:
        db_word.category = word_update.category

    session.add(db_word)
    session.commit()
    session.refresh(db_word)
    return db_word


@router.delete("/{word_id}")
def delete_word(
    word_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    db_word = get_user_word(word_id, current_user.id, session)  # type: ignore
    session.delete(db_word)
    session.commit()
    return {"message": "Deleted successfully"}


@router.patch("/{word_id}/toggle_learned", response_model=WordRead)
def toggle_learned(
    word_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Word:
    db_word = get_user_word(word_id, current_user.id, session)  # type: ignore
    db_word.is_learned = not db_word.is_learned
    session.add(db_word)
    session.commit()
    session.refresh(db_word)
    return db_word
