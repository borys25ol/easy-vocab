from datetime import timedelta

from app.core.security import (
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


def test_jwt_tokens() -> None:
    subject = "testuser"
    token = create_access_token(subject=subject)
    assert token is not None

    decoded_subject = decode_access_token(token)
    assert decoded_subject == subject


def test_jwt_token_expiration() -> None:
    subject = "testuser"
    # Create an expired token
    token = create_access_token(subject=subject, expires_delta=timedelta(seconds=-1))
    decoded_subject = decode_access_token(token)
    assert decoded_subject is None
