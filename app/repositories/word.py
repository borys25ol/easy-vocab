from collections.abc import Sequence
from typing import Any, cast

from sqlmodel import Session, select, true

from app.models.word import Word
from app.schemas.word import WordUpdate


class WordRepository:
    """Data access for Word entities."""

    def list_for_user(self, session: Session, user_id: int) -> Sequence[Word]:
        """Return all words for a user ordered by creation time."""
        statement = (
            select(Word)
            .where(Word.user_id == user_id)
            .order_by(cast(Any, Word.created_at).desc())
        )
        return session.exec(statement).all()

    def get_by_id_for_user(
        self, session: Session, word_id: int, user_id: int
    ) -> Word | None:
        """Fetch a word by id scoped to a user."""
        db_word = session.get(entity=Word, ident=word_id)
        if not db_word or db_word.user_id != user_id:
            return None
        return db_word

    def create_for_user(
        self,
        session: Session,
        user_id: int,
        word_text: str,
        word_info: dict[str, Any],
    ) -> Word:
        """Create a word for a user from enriched metadata."""
        new_word = Word(
            user_id=user_id,
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

    def list_phrasal_roots(self, session: Session, user_id: int) -> list[str]:
        """List distinct phrasal verb roots for a user."""
        statement = (
            select(Word).where(Word.user_id == user_id).where(Word.is_phrasal == true())
        )
        phrasal_verbs = session.exec(statement).all()

        roots = set()
        for verb in phrasal_verbs:
            parts = verb.word.split()
            if parts:
                roots.add(parts[0].strip().capitalize())

        return sorted(roots)

    def list_phrasal_verbs(
        self, session: Session, user_id: int, root: str
    ) -> Sequence[Word]:
        """List phrasal verbs for a root and user."""
        search_pattern = f"{root.lower()} %"
        word_column = cast(Any, Word.word)
        statement = (
            select(Word)
            .where(Word.user_id == user_id)
            .where(word_column.like(search_pattern))
            .where(Word.is_phrasal == true())
        )
        return session.exec(statement).all()

    def list_idioms(self, session: Session, user_id: int) -> Sequence[Word]:
        """List idioms for a user ordered by creation time."""
        statement = (
            select(Word)
            .where(Word.user_id == user_id)
            .where(Word.is_idiom == true())
            .order_by(cast(Any, Word.created_at).desc())
        )
        return session.exec(statement).all()

    def update_word(
        self, session: Session, word: Word, word_update: WordUpdate
    ) -> Word:
        """Apply allowed updates to a word."""
        if word_update.word is not None:
            word.word = word_update.word
        if word_update.translation is not None:
            word.translation = word_update.translation
        if word_update.category is not None:
            word.category = word_update.category

        session.add(word)
        session.commit()
        session.refresh(word)
        return word

    def delete_word(self, session: Session, word: Word) -> None:
        """Delete a word and persist the change."""
        session.delete(word)
        session.commit()

    def toggle_learned(self, session: Session, word: Word) -> Word:
        """Toggle learned status for a word."""
        word.is_learned = not word.is_learned
        session.add(word)
        session.commit()
        session.refresh(word)
        return word
