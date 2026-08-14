import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_refuses_default_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("OPENROUTER_API_KEY", "a-real-key")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None)

    assert "SECRET_KEY" in str(excinfo.value)


def test_production_refuses_default_openrouter_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None)

    assert "OPENROUTER_API_KEY" in str(excinfo.value)


def test_development_allows_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.SECRET_KEY == "dev_secret_key_change_me"
