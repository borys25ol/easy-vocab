import base64
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any, NamedTuple

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


# A hash of a random string that was never recorded. Login verifies against
# it when the username does not exist, so an unknown username costs the same
# bcrypt round as a wrong password and stops leaking which accounts are real.
DUMMY_PASSWORD_HASH = (
    "sha256$$2b$12$HQ29RsMX1HANKX05SYAV7.g0c4XeVHIHzHO3kdp9CKcyFqbxxeaS."
)


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


def hash_mcp_api_key(api_key: str) -> str:
    """Hash an MCP key for storage.

    Plain SHA-256 rather than bcrypt: the key is 256 bits of output from
    secrets.token_urlsafe, so there is no guessable input to slow down, and
    every MCP call would otherwise pay for a bcrypt round.
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


class TokenPayload(NamedTuple):
    """The claims the application acts on."""

    subject: str
    version: int


def create_access_token(
    subject: str | Any,
    token_version: int,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "ver": token_version}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenPayload | None:
    """Return the claims of a valid token, or None for any invalid one.

    A signed token can still be unusable, for example when it carries no sub
    or no ver claim. Callers treat None as "not authenticated", so a missing
    claim must return None rather than raise and turn a 401 into a 500.

    A token minted before ver existed cannot be revoked, so it is refused too.
    That costs everyone one sign in on the deploy that introduces the claim.
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(
            subject=decoded_token["sub"],
            version=int(decoded_token["ver"]),
        )
    except (jwt.JWTError, KeyError, TypeError, ValueError):
        return None
