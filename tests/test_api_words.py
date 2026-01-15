from unittest.mock import patch

from fastapi.testclient import TestClient


def test_read_words_empty(client: TestClient):
    response = client.get("/words/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_word(client: TestClient):
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
    with patch(
        "app.api.endpoints.words.get_usage_examples", return_value=mock_data
    ):
        response = client.post("/words/", params={"word": "TestWord"})

    assert response.status_code == 200
    data = response.json()
    assert data["word"] == "testword"
    assert data["translation"] == "тест"
    assert data["id"] is not None


def test_create_and_read_word(client: TestClient):
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

    with patch(
        "app.api.endpoints.words.get_usage_examples", return_value=mock_data
    ):
        client.post("/words/", params={"word": "TestWord"})

    response = client.get("/words/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["word"] == "testword"
