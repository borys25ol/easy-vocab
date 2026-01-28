import datetime

from sqlmodel import Session

from app.models.word import Word
from app.repositories.word import WordRepository


def create_word(
    session: Session,
    *,
    user_id: int,
    word: str,
    category: str = "Nouns",
    level: str = "A1",
    is_learned: bool = False,
    is_phrasal: bool = False,
    is_idiom: bool = False,
    created_at: datetime.datetime | None = None,
) -> Word:
    word_entity = Word(
        user_id=user_id,
        word=word,
        translation="translation",
        examples=None,
        synonyms=None,
        rank=100,
        rank_range="1-500",
        level=level,
        frequency=5,
        frequency_group="Core",
        category=category,
        type="word",
        is_phrasal=is_phrasal,
        is_idiom=is_idiom,
        is_learned=is_learned,
        created_at=created_at
        if created_at is not None
        else datetime.datetime.now(datetime.UTC),
    )
    session.add(word_entity)
    session.commit()
    session.refresh(word_entity)
    return word_entity


def test_list_for_user_with_pagination(session: Session) -> None:
    repo = WordRepository()
    create_word(
        session,
        user_id=1,
        word="alpha",
        created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
    )
    create_word(
        session,
        user_id=1,
        word="bravo",
        created_at=datetime.datetime(2024, 1, 2, tzinfo=datetime.UTC),
    )
    create_word(
        session,
        user_id=1,
        word="charlie",
        created_at=datetime.datetime(2024, 1, 3, tzinfo=datetime.UTC),
    )
    create_word(
        session,
        user_id=2,
        word="delta",
        created_at=datetime.datetime(2024, 1, 4, tzinfo=datetime.UTC),
    )

    words = repo.list_for_user(session, user_id=1, limit=2, offset=0)
    assert [word.word for word in words] == ["charlie", "bravo"]

    words = repo.list_for_user(session, user_id=1, limit=2, offset=2)
    assert [word.word for word in words] == ["alpha"]


def test_count_for_user_filters(session: Session) -> None:
    repo = WordRepository()
    create_word(session, user_id=1, word="alpha", category="Verbs", level="B1")
    create_word(
        session,
        user_id=1,
        word="bravo",
        category="Verbs",
        level="B1",
        is_learned=True,
    )
    create_word(session, user_id=1, word="charlie", category="Nouns", level="A2")
    create_word(session, user_id=2, word="delta", category="Verbs", level="B1")

    assert repo.count_for_user(session, user_id=1) == 3
    assert (
        repo.count_for_user(
            session,
            user_id=1,
            category="Verbs",
            level="B1",
        )
        == 2
    )
    assert (
        repo.count_for_user(
            session,
            user_id=1,
            category="Verbs",
            level="B1",
            is_learned=True,
        )
        == 1
    )


def test_list_idioms_and_count(session: Session) -> None:
    repo = WordRepository()
    create_word(session, user_id=1, word="alpha", is_idiom=True)
    create_word(session, user_id=1, word="bravo", is_idiom=False)
    create_word(session, user_id=2, word="charlie", is_idiom=True)

    idioms = repo.list_idioms(session, user_id=1)
    assert [word.word for word in idioms] == ["alpha"]
    assert repo.count_idioms(session, user_id=1) == 1


def test_list_phrasal_verbs_and_count(session: Session) -> None:
    repo = WordRepository()
    create_word(session, user_id=1, word="get up", is_phrasal=True)
    create_word(session, user_id=1, word="get over", is_phrasal=True)
    create_word(session, user_id=1, word="take off", is_phrasal=True)
    create_word(session, user_id=1, word="get", is_phrasal=True)
    create_word(session, user_id=2, word="get down", is_phrasal=True)

    phrasal = repo.list_phrasal_verbs(session, user_id=1, root="get")
    assert {word.word for word in phrasal} == {"get up", "get over"}
    assert repo.count_phrasal_verbs(session, user_id=1, root="get") == 2


def test_get_by_word_for_user(session: Session) -> None:
    repo = WordRepository()
    create_word(session, user_id=1, word="testword")
    found = repo.get_by_word_for_user(session, user_id=1, word_text="TestWord")
    assert found is not None
    assert found.word == "testword"
