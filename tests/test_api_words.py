from unittest.mock import patch

from fastapi.testclient import TestClient

from app.schemas.word import WordInfo


def make_word_info(
    word: str = "testword",
    *,
    category: str = "Nouns",
    level: str = "A1",
) -> WordInfo:
    return WordInfo(
        word=word,
        rank=100,
        rank_range="1-500",
        translation="тест",
        category=category,
        level=level,
        type="word",
        frequency=5,
        frequency_group="Core",
        examples="Example 1",
        is_phrasal=False,
        is_idiom=False,
        synonyms="test1, test2",
    )


def test_read_words_empty(auth_client: TestClient) -> None:
    response = auth_client.get("/words/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["offset"] == 0


def test_unauthorized_access(client: TestClient) -> None:
    response = client.get("/words/")
    assert response.status_code == 401


def test_create_word(auth_client: TestClient) -> None:
    # Patch where it is imported in the endpoint module
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("testword"),
    ):
        response = auth_client.post("/words/", json={"word": "TestWord"})

    assert response.status_code == 200
    data = response.json()
    assert data["word"] == "testword"
    assert data["translation"] == "тест"
    assert data["id"] is not None


def test_create_and_read_word(auth_client: TestClient) -> None:
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("testword"),
    ):
        auth_client.post("/words/", json={"word": "TestWord"})

    response = auth_client.get("/words/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["word"] == "testword"


# Multi-user isolation tests


def test_user_cannot_see_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 1 cannot see words created by user 2."""
    # User 1 creates a word
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("useroneword"),
    ):
        response = auth_client.post("/words/", json={"word": "UserOneWord"})
    assert response.status_code == 200

    # User 2 should NOT see user 1's word
    response = auth_client_2.get("/words/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []

    # User 1 should see their own word
    response = auth_client.get("/words/")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_user_cannot_delete_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 2 cannot delete words created by user 1."""
    # User 1 creates a word
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("protectedword"),
    ):
        response = auth_client.post("/words/", json={"word": "ProtectedWord"})
    assert response.status_code == 200
    word_id = response.json()["id"]

    # User 2 tries to delete user 1's word - should get 404
    response = auth_client_2.delete(f"/words/{word_id}")
    assert response.status_code == 404

    # Word should still exist for user 1
    response = auth_client.get("/words/")
    assert len(response.json()["items"]) == 1


def test_user_cannot_update_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 2 cannot update words created by user 1."""
    # User 1 creates a word
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("originalword"),
    ):
        response = auth_client.post("/words/", json={"word": "OriginalWord"})
    assert response.status_code == 200
    word_id = response.json()["id"]

    # User 2 tries to update user 1's word - should get 404
    response = auth_client_2.put(
        f"/words/{word_id}",
        json={"word": "hacked", "translation": "hacked", "category": "Hacked"},
    )
    assert response.status_code == 404

    # Word should still have original value for user 1
    response = auth_client.get("/words/")
    assert response.json()["items"][0]["word"] == "originalword"


def test_user_cannot_toggle_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 2 cannot toggle learned status on user 1's words."""
    # User 1 creates a word
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("learnme"),
    ):
        response = auth_client.post("/words/", json={"word": "LearnMe"})
    assert response.status_code == 200
    word_id = response.json()["id"]

    # User 2 tries to toggle user 1's word - should get 404
    response = auth_client_2.patch(f"/words/{word_id}/toggle_learned")
    assert response.status_code == 404

    # Word should still be is_learned=False for user 1
    response = auth_client.get("/words/")
    assert response.json()["items"][0]["is_learned"] is False


def test_words_pagination_and_total(auth_client: TestClient) -> None:
    word_infos = [make_word_info(f"word-{i}") for i in range(5)]
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        side_effect=word_infos,
    ):
        for i in range(5):
            response = auth_client.post("/words/", json={"word": f"Word{i}"})
            assert response.status_code == 200

    response = auth_client.get("/words/?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    response = auth_client.get("/words/?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2
    assert len(data["items"]) == 2


def test_words_filters_total(auth_client: TestClient) -> None:
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("alpha", category="Verbs", level="B1"),
    ):
        response = auth_client.post("/words/", json={"word": "Alpha"})
        assert response.status_code == 200

    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("beta", category="Nouns", level="A1"),
    ):
        response = auth_client.post("/words/", json={"word": "Beta"})
        assert response.status_code == 200

    response = auth_client.get("/words/?category=Verbs&level=B1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["word"] == "alpha"


def test_create_word_duplicate_returns_conflict(auth_client: TestClient) -> None:
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("duplicate"),
    ):
        response = auth_client.post("/words/", json={"word": "Duplicate"})
        assert response.status_code == 200

        response = auth_client.post("/words/", json={"word": "Duplicate"})
        assert response.status_code == 409

    response = auth_client.get("/words/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_word_creation_flow_updates_total(auth_client: TestClient) -> None:
    with patch(
        "app.api.endpoints.words.get_usage_examples",
        return_value=make_word_info("flowword"),
    ):
        response = auth_client.post("/words/", json={"word": "FlowWord"})
        assert response.status_code == 200

    response = auth_client.get("/words/?limit=50&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert data["items"][0]["word"] == "flowword"
