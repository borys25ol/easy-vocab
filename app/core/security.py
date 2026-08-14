import base64
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings


# Pinned on purpose. The signing algorithm is a security property, not a
# deployment knob: an env var that flips it to "none" would forge every token.
ALGORITHM = "HS256"

# Marks a hash whose password was folded through SHA-256 first. Bare bcrypt
# reads at most 72 bytes, so without the fold two long passwords sharing a
# 72-byte prefix authenticate each other. Hashes written before this scheme
# start with "$2" and are still accepted, so no stored password breaks.
_SHA256_SCHEME_PREFIX = "sha256$"


def _prehash(password: str) -> bytes:
    """Fold a password of any length into 44 bcrypt-safe bytes.

    The digest is base64 encoded because bcrypt stops at the first NUL byte,
    which a raw digest can easily contain.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith(_SHA256_SCHEME_PREFIX):
        candidate = _prehash(plain_password)
        stored = hashed_password[len(_SHA256_SCHEME_PREFIX) :]
    else:
        # Legacy hash written by passlib: bcrypt over the raw password.
        candidate = plain_password.encode("utf-8")
        stored = hashed_password

    try:
        return bcrypt.checkpw(candidate, stored.encode("utf-8"))
    except ValueError:
        # Malformed hash in the database must read as "wrong password".
        return False


def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(_prehash(password), bcrypt.gensalt())
    return _SHA256_SCHEME_PREFIX + hashed.decode("utf-8")


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> str | None:
    """Return the subject of a valid token, or None for any invalid one.

    A signed token can still be unusable, for example when it carries no sub
    claim. Callers treat None as "not authenticated", so a missing claim must
    return None rather than raise and turn a 401 into a 500.
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token["sub"]
    except (jwt.JWTError, KeyError):
        return None
