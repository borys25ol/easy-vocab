from fastapi.testclient import TestClient


def test_home_page_renders(auth_client: TestClient) -> None:
    response = auth_client.get("/")
    assert response.status_code == 200
    assert 'id="wordsList"' in response.text


def test_quiz_page_renders(auth_client: TestClient) -> None:
    response = auth_client.get("/quiz")
    assert response.status_code == 200
    assert 'id="quizCard"' in response.text


def test_quiz_translate_page_renders(auth_client: TestClient) -> None:
    response = auth_client.get("/quiz_translate")
    assert response.status_code == 200
    assert 'id="quizCard"' in response.text


def test_flashcards_page_renders(auth_client: TestClient) -> None:
    response = auth_client.get("/flashcards")
    assert response.status_code == 200
    assert 'id="flashcard"' in response.text


def test_phrasal_page_renders(auth_client: TestClient) -> None:
    response = auth_client.get("/phrasal")
    assert response.status_code == 200
    assert 'id="phrasalList"' in response.text


def test_idioms_page_renders(auth_client: TestClient) -> None:
    response = auth_client.get("/idioms")
    assert response.status_code == 200
    assert 'id="idiomsList"' in response.text


def test_login_page_renders(client: TestClient) -> None:
    response = client.get("/login")
    assert response.status_code == 200
    assert 'id="username"' in response.text
