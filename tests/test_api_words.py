from unittest.mock import patch

from fastapi.testclient import TestClient


def test_read_words_empty(auth_client: TestClient) -> None:
    response = auth_client.get("/words/")
    assert response.status_code == 200
    assert response.json() == []


def test_unauthorized_access(client: TestClient) -> None:
    response = client.get("/words/")
    assert response.status_code == 401


def test_create_word(auth_client: TestClient) -> None:
    mock_data = {
        "rank": 100,
        "rank_range": "1-500",
        "translation": "тест",
        "category": "Nouns",
        "level": "A1",
        "type": "word",
        "frequency": 5,
        "frequency_group": "Core",
        "examples": "Example 1",
        "is_phrasal": False,
        "is_idiom": False,
        "synonyms": "test1, test2",
    }

    # Patch where it is imported in the endpoint module
    with patch("app.api.endpoints.words.get_usage_examples", return_value=mock_data):
        response = auth_client.post("/words/", params={"word": "TestWord"})

    assert response.status_code == 200
    data = response.json()
    assert data["word"] == "testword"
    assert data["translation"] == "тест"
    assert data["id"] is not None


def test_create_and_read_word(auth_client: TestClient) -> None:
    mock_data = {
        "rank": 100,
        "rank_range": "1-500",
        "translation": "тест",
        "category": "Nouns",
        "level": "A1",
        "type": "word",
        "frequency": 5,
        "frequency_group": "Core",
        "examples": "Example 1",
        "is_phrasal": False,
        "is_idiom": False,
        "synonyms": "test1, test2",
    }

    with patch("app.api.endpoints.words.get_usage_examples", return_value=mock_data):
        auth_client.post("/words/", params={"word": "TestWord"})

    response = auth_client.get("/words/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["word"] == "testword"


# Multi-user isolation tests


def test_user_cannot_see_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 1 cannot see words created by user 2."""
    mock_data = {
        "rank": 100,
        "rank_range": "1-500",
        "translation": "тест",
        "category": "Nouns",
        "level": "A1",
        "type": "word",
        "frequency": 5,
        "frequency_group": "Core",
        "examples": "Example 1",
        "is_phrasal": False,
        "is_idiom": False,
        "synonyms": "test1, test2",
    }

    # User 1 creates a word
    with patch("app.api.endpoints.words.get_usage_examples", return_value=mock_data):
        response = auth_client.post("/words/", params={"word": "UserOneWord"})
    assert response.status_code == 200

    # User 2 should NOT see user 1's word
    response = auth_client_2.get("/words/")
    assert response.status_code == 200
    assert response.json() == []

    # User 1 should see their own word
    response = auth_client.get("/words/")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_user_cannot_delete_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 2 cannot delete words created by user 1."""
    mock_data = {
        "rank": 100,
        "rank_range": "1-500",
        "translation": "тест",
        "category": "Nouns",
        "level": "A1",
        "type": "word",
        "frequency": 5,
        "frequency_group": "Core",
        "examples": "Example 1",
        "is_phrasal": False,
        "is_idiom": False,
        "synonyms": "test1, test2",
    }

    # User 1 creates a word
    with patch("app.api.endpoints.words.get_usage_examples", return_value=mock_data):
        response = auth_client.post("/words/", params={"word": "ProtectedWord"})
    assert response.status_code == 200
    word_id = response.json()["id"]

    # User 2 tries to delete user 1's word - should get 404
    response = auth_client_2.delete(f"/words/{word_id}")
    assert response.status_code == 404

    # Word should still exist for user 1
    response = auth_client.get("/words/")
    assert len(response.json()) == 1


def test_user_cannot_update_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 2 cannot update words created by user 1."""
    mock_data = {
        "rank": 100,
        "rank_range": "1-500",
        "translation": "тест",
        "category": "Nouns",
        "level": "A1",
        "type": "word",
        "frequency": 5,
        "frequency_group": "Core",
        "examples": "Example 1",
        "is_phrasal": False,
        "is_idiom": False,
        "synonyms": "test1, test2",
    }

    # User 1 creates a word
    with patch("app.api.endpoints.words.get_usage_examples", return_value=mock_data):
        response = auth_client.post("/words/", params={"word": "OriginalWord"})
    assert response.status_code == 200
    word_id = response.json()["id"]

    # User 2 tries to update user 1's word - should get 404
    response = auth_client_2.put(
        f"/words/{word_id}",
        params={"word": "hacked", "translation": "hacked", "category": "Hacked"},
    )
    assert response.status_code == 404

    # Word should still have original value for user 1
    response = auth_client.get("/words/")
    assert response.json()[0]["word"] == "originalword"


def test_user_cannot_toggle_other_users_words(
    auth_client: TestClient, auth_client_2: TestClient
) -> None:
    """Test that user 2 cannot toggle learned status on user 1's words."""
    mock_data = {
        "rank": 100,
        "rank_range": "1-500",
        "translation": "тест",
        "category": "Nouns",
        "level": "A1",
        "type": "word",
        "frequency": 5,
        "frequency_group": "Core",
        "examples": "Example 1",
        "is_phrasal": False,
        "is_idiom": False,
        "synonyms": "test1, test2",
    }

    # User 1 creates a word
    with patch("app.api.endpoints.words.get_usage_examples", return_value=mock_data):
        response = auth_client.post("/words/", params={"word": "LearnMe"})
    assert response.status_code == 200
    word_id = response.json()["id"]

    # User 2 tries to toggle user 1's word - should get 404
    response = auth_client_2.patch(f"/words/{word_id}/toggle_learned")
    assert response.status_code == 404

    # Word should still be is_learned=False for user 1
    response = auth_client.get("/words/")
    assert response.json()[0]["is_learned"] is False
