from collections.abc import Sequence
from typing import Any

from sqlmodel import Session, col, func, select, true

from app.models.word import Word
from app.schemas.word import WordInfo, WordUpdate


class WordRepository:
    """Data access for Word entities."""

    def list_for_user(
        self,
        session: Session,
        user_id: int,
        *,
        limit: int | None = None,
        offset: int = 0,
        category: str | None = None,
        level: str | None = None,
        is_learned: bool | None = None,
        sort: str = "date",
    ) -> Sequence[Word]:
        """Return words for a user with optional filters and sorting.

        Args:
            session: Active database session.
            user_id: Owner of the words.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.
            category: Optional category filter.
            level: Optional level filter (substring match).
            is_learned: Optional learned flag filter.
            sort: Sorting mode ("date" or "rank").

        Returns:
            List of matching Word records.
        """
        statement = select(Word)
        statement = self._apply_filters(
            statement,
            user_id=user_id,
            category=category,
            level=level,
            is_learned=is_learned,
        )
        if sort == "rank":
            statement = statement.order_by(
                col(Word.is_learned),
                col(Word.rank),
                col(Word.created_at).desc(),
            )
        else:
            statement = statement.order_by(
                col(Word.is_learned),
                col(Word.created_at).desc(),
            )
        statement = self._apply_pagination(statement, limit=limit, offset=offset)
        return session.exec(statement).all()

    def get_by_word_for_user(
        self, session: Session, user_id: int, word_text: str
    ) -> Word | None:
        """Fetch a word by text scoped to a user.

        Args:
            session: Active database session.
            user_id: Owner of the words.
            word_text: Word or phrase to match.

        Returns:
            Matching Word if found, otherwise None.
        """
        statement = (
            select(Word)
            .where(Word.user_id == user_id)
            .where(Word.word == word_text.lower())
        )
        return session.exec(statement).first()

    def count_for_user(
        self,
        session: Session,
        user_id: int,
        *,
        category: str | None = None,
        level: str | None = None,
        is_learned: bool | None = None,
    ) -> int:
        """Count words for a user with optional filters.

        Args:
            session: Active database session.
            user_id: Owner of the words.
            category: Optional category filter.
            level: Optional level filter (substring match).
            is_learned: Optional learned flag filter.

        Returns:
            Count of matching words.
        """
        statement = select(func.count()).select_from(Word)
        statement = self._apply_filters(
            statement,
            user_id=user_id,
            category=category,
            level=level,
            is_learned=is_learned,
        )
        return int(session.exec(statement).one())

    def get_by_id_for_user(
        self, session: Session, word_id: int, user_id: int
    ) -> Word | None:
        """Fetch a word by id scoped to a user.

        Args:
            session: Active database session.
            word_id: Word identifier.
            user_id: Owner of the word.

        Returns:
            Matching Word if found, otherwise None.
        """
        db_word = session.get(entity=Word, ident=word_id)
        if not db_word or db_word.user_id != user_id:
            return None
        return db_word

    def create_for_user(
        self,
        session: Session,
        user_id: int,
        word_text: str,
        word_info: WordInfo,
    ) -> Word:
        """Create a word for a user from enriched metadata.

        Args:
            session: Active database session.
            user_id: Owner of the word.
            word_text: Raw word text input.
            word_info: Enriched word metadata.

        Returns:
            Newly created Word.
        """
        new_word = Word(
            user_id=user_id,
            word=word_text.lower(),
            translation=word_info.translation,
            examples=word_info.examples,
            synonyms=word_info.synonyms,
            rank=word_info.rank,
            rank_range=word_info.rank_range,
            category=word_info.category,
            level=word_info.level,
            type=word_info.type,
            frequency=word_info.frequency,
            frequency_group=word_info.frequency_group,
            is_phrasal=word_info.is_phrasal,
            is_idiom=word_info.is_idiom,
        )
        session.add(new_word)
        session.commit()
        session.refresh(new_word)
        return new_word

    def list_phrasal_roots(self, session: Session, user_id: int) -> list[str]:
        """List distinct phrasal verb roots for a user.

        Args:
            session: Active database session.
            user_id: Owner of the words.

        Returns:
            Sorted list of unique phrasal roots.
        """
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
        self,
        session: Session,
        user_id: int,
        root: str,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[Word]:
        """List phrasal verbs for a root and user.

        Args:
            session: Active database session.
            user_id: Owner of the words.
            root: Root verb to match.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.

        Returns:
            List of matching phrasal verbs.
        """
        search_pattern = f"{root.lower()} %"
        word_column = col(Word.word)
        statement = (
            select(Word)
            .where(Word.user_id == user_id)
            .where(word_column.like(search_pattern))
            .where(Word.is_phrasal == true())
            .order_by(col(Word.created_at).desc())
        )
        statement = self._apply_pagination(statement, limit=limit, offset=offset)
        return session.exec(statement).all()

    def count_phrasal_verbs(self, session: Session, user_id: int, root: str) -> int:
        """Count phrasal verbs for a root and user.

        Args:
            session: Active database session.
            user_id: Owner of the words.
            root: Root verb to match.

        Returns:
            Count of matching phrasal verbs.
        """
        search_pattern = f"{root.lower()} %"
        word_column = col(Word.word)
        statement = (
            select(func.count())
            .select_from(Word)
            .where(Word.user_id == user_id)
            .where(word_column.like(search_pattern))
            .where(Word.is_phrasal == true())
        )
        return int(session.exec(statement).one())

    def list_idioms(
        self,
        session: Session,
        user_id: int,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[Word]:
        """List idioms for a user ordered by creation time.

        Args:
            session: Active database session.
            user_id: Owner of the words.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.

        Returns:
            List of matching idioms.
        """
        statement = (
            select(Word)
            .where(Word.user_id == user_id)
            .where(Word.is_idiom == true())
            .order_by(col(Word.created_at).desc())
        )
        statement = self._apply_pagination(statement, limit=limit, offset=offset)
        return session.exec(statement).all()

    def count_idioms(self, session: Session, user_id: int) -> int:
        """Count idioms for a user.

        Args:
            session: Active database session.
            user_id: Owner of the words.

        Returns:
            Count of matching idioms.
        """
        statement = (
            select(func.count())
            .select_from(Word)
            .where(Word.user_id == user_id)
            .where(Word.is_idiom == true())
        )
        return int(session.exec(statement).one())

    def update_word(
        self, session: Session, word: Word, word_update: WordUpdate
    ) -> Word:
        """Apply allowed updates to a word.

        Args:
            session: Active database session.
            word: Word entity to update.
            word_update: Update payload.

        Returns:
            Updated Word.
        """
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
        """Delete a word and persist the change.

        Args:
            session: Active database session.
            word: Word entity to delete.
        """
        session.delete(word)
        session.commit()

    def toggle_learned(self, session: Session, word: Word) -> Word:
        """Toggle learned status for a word.

        Args:
            session: Active database session.
            word: Word entity to toggle.

        Returns:
            Updated Word with toggled learned status.
        """
        word.is_learned = not word.is_learned
        session.add(word)
        session.commit()
        session.refresh(word)
        return word

    @staticmethod
    def _apply_filters(
        statement: Any,
        *,
        user_id: int,
        category: str | None = None,
        level: str | None = None,
        is_learned: bool | None = None,
    ) -> Any:
        """Apply common Word filters to a statement.

        Args:
            statement: SQLModel statement to update.
            user_id: Owner of the words.
            category: Optional category filter.
            level: Optional level filter (substring match).
            is_learned: Optional learned flag filter.

        Returns:
            Updated statement with filters applied.
        """
        statement = statement.where(Word.user_id == user_id)
        if category:
            statement = statement.where(Word.category == category)
        if level:
            level_column = col(Word.level)
            statement = statement.where(level_column.like(f"%{level}%"))
        if is_learned is not None:
            statement = statement.where(Word.is_learned == is_learned)
        return statement

    @staticmethod
    def _apply_pagination(statement: Any, *, limit: int | None, offset: int) -> Any:
        """Apply limit/offset pagination to a statement.

        Args:
            statement: SQLModel statement to update.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.

        Returns:
            Updated statement with pagination applied.
        """
        if offset:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        return statement
