from collections.abc import Sequence
from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import get_current_user, get_word_repository
from app.core.database import get_session
from app.models.user import User
from app.models.word import Word
from app.repositories.word import WordRepository
from app.schemas.word import WordCreate, WordListResponse, WordRead, WordUpdate
from app.services.genai_service import get_usage_examples


router = APIRouter(dependencies=[Depends(get_current_user)])


def _require_user_id(user: User) -> int:
    if user.id is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user.id


@router.get("", response_model=WordListResponse)
def get_words(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    level: str | None = Query(default=None),
    is_learned: bool | None = Query(default=None),
    sort: Literal["date", "rank"] = Query(default="date"),
) -> WordListResponse:
    """List all words for the current user."""
    user_id = _require_user_id(current_user)
    items = word_repo.list_for_user(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        category=category,
        level=level,
        is_learned=is_learned,
        sort=sort,
    )
    total = word_repo.count_for_user(
        session=session,
        user_id=user_id,
        category=category,
        level=level,
        is_learned=is_learned,
    )
    return WordListResponse(
        items=cast(Sequence[WordRead], items),
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=WordRead)
def create_word(
    word_in: WordCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
) -> Word:
    """Create a new word with AI enrichment."""
    user_id = _require_user_id(current_user)
    word_text = word_in.word
    word_info = get_usage_examples(word=word_text)
    return word_repo.create_for_user(
        session=session,
        user_id=user_id,
        word_text=word_text,
        word_info=word_info,
    )


@router.get("/phrasal_roots")
def get_phrasal_roots(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
) -> list[str]:
    """
    Extracts unique roots ONLY from words marked as is_phrasal for current user.
    """
    user_id = _require_user_id(current_user)
    return word_repo.list_phrasal_roots(session=session, user_id=user_id)


@router.get("/phrasal/{root}", response_model=WordListResponse)
def get_phrasal_verbs(
    root: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
) -> WordListResponse:
    """
    Fetches phrasal verbs by root and strict is_phrasal flag for current user.
    """
    user_id = _require_user_id(current_user)
    items = word_repo.list_phrasal_verbs(
        session=session,
        user_id=user_id,
        root=root,
        limit=limit,
        offset=offset,
    )
    total = word_repo.count_phrasal_verbs(
        session=session,
        user_id=user_id,
        root=root,
    )
    return WordListResponse(
        items=cast(Sequence[WordRead], items),
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/idioms", response_model=WordListResponse)
def get_idioms(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
) -> WordListResponse:
    """
    Fetches all words marked as idioms for current user.
    """
    user_id = _require_user_id(current_user)
    items = word_repo.list_idioms(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    total = word_repo.count_idioms(session=session, user_id=user_id)
    return WordListResponse(
        items=cast(Sequence[WordRead], items),
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put("/{word_id}", response_model=WordRead)
def update_word(
    word_id: int,
    word_update: WordUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
) -> Word:
    """Update editable fields for a word."""
    user_id = _require_user_id(current_user)
    db_word = word_repo.get_by_id_for_user(
        session=session,
        word_id=word_id,
        user_id=user_id,
    )
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")
    return word_repo.update_word(
        session=session,
        word=db_word,
        word_update=word_update,
    )


@router.delete("/{word_id}")
def delete_word(
    word_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
) -> dict[str, str]:
    """Delete a word owned by the current user."""
    user_id = _require_user_id(current_user)
    db_word = word_repo.get_by_id_for_user(
        session=session,
        word_id=word_id,
        user_id=user_id,
    )
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")
    word_repo.delete_word(session=session, word=db_word)
    return {"message": "Deleted successfully"}


@router.patch("/{word_id}/toggle_learned", response_model=WordRead)
def toggle_learned(
    word_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    word_repo: WordRepository = Depends(get_word_repository),
) -> Word:
    """Toggle the learned flag for a word."""
    user_id = _require_user_id(current_user)
    db_word = word_repo.get_by_id_for_user(
        session=session,
        word_id=word_id,
        user_id=user_id,
    )
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")
    return word_repo.toggle_learned(session=session, word=db_word)
