from datetime import timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing() -> None:
    password = "secret_password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_long_password_is_not_truncated() -> None:
    """Raw bcrypt stops at 72 bytes, which makes long passwords interchangeable."""
    hashed = get_password_hash("x" * 80)

    assert verify_password("x" * 80, hashed) is True
    assert verify_password("x" * 72, hashed) is False


def test_legacy_bcrypt_hash_still_verifies() -> None:
    """Hashes written before the scheme change must keep working."""
    import bcrypt

    legacy = bcrypt.hashpw(b"testpassword", bcrypt.gensalt()).decode()
    assert legacy.startswith("$2")

    assert verify_password("testpassword", legacy) is True
    assert verify_password("wrong", legacy) is False


def test_passlib_is_not_imported() -> None:
    """passlib is unmaintained and logs a traceback against modern bcrypt."""
    import sys

    import app.core.security  # noqa: F401

    assert "passlib" not in sys.modules


def test_jwt_tokens() -> None:
    subject = "testuser"
    token = create_access_token(subject=subject, token_version=3)
    assert token is not None

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.subject == subject
    assert payload.version == 3


def test_jwt_token_expiration() -> None:
    subject = "testuser"
    # Create an expired token
    token = create_access_token(
        subject=subject, token_version=0, expires_delta=timedelta(seconds=-1)
    )
    assert decode_access_token(token) is None


def test_jwt_token_without_subject_is_rejected() -> None:
    """A signed token missing the sub claim must not raise."""
    token = jwt.encode({"foo": "bar"}, settings.SECRET_KEY, algorithm=ALGORITHM)

    assert decode_access_token(token) is None


def test_jwt_algorithm_is_not_configurable() -> None:
    """Pinning the algorithm keeps a stray env var from weakening the token."""
    from app.core.config import Settings

    assert "ALGORITHM" not in Settings.model_fields
    assert ALGORITHM == "HS256"
