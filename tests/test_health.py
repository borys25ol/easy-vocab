from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_needs_no_authentication(client: TestClient) -> None:
    # The probe runs without credentials. A 401 here would make every pod
    # look unhealthy forever.
    response = client.get("/health")
    assert response.status_code != 401
