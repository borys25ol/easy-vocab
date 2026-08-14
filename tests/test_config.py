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


def test_production_refuses_default_postgres_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    monkeypatch.setenv("OPENROUTER_API_KEY", "a-real-key")
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None)

    assert "POSTGRES_PASSWORD" in str(excinfo.value)


def test_samesite_none_needs_an_explicit_acknowledgement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SameSite=none removes the browser-side CSRF defence, so make it loud."""
    monkeypatch.setenv("COOKIE_SAMESITE", "none")
    monkeypatch.delenv("COOKIE_SAMESITE_NONE_ACKNOWLEDGED", raising=False)

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None)

    assert "COOKIE_SAMESITE" in str(excinfo.value)


def test_samesite_none_is_allowed_once_acknowledged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COOKIE_SAMESITE", "none")
    monkeypatch.setenv("COOKIE_SAMESITE_NONE_ACKNOWLEDGED", "true")

    settings = Settings(_env_file=None)

    assert settings.COOKIE_SAMESITE == "none"


def test_development_allows_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.SECRET_KEY == "dev_secret_key_change_me"
