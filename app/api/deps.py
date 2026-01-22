from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.word import WordRepository


def get_user_repository() -> UserRepository:
    """Provide user repository instance."""
    return UserRepository()


def get_word_repository() -> WordRepository:
    """Provide word repository instance."""
    return WordRepository()


async def get_current_user(
    request: Request,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """Return the authenticated user from the session cookie."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    username = decode_access_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    user = user_repo.get_by_username(session=db, username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User | None:
    """Return the authenticated user if present."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None

    username = decode_access_token(token)
    if not username:
        return None

    return user_repo.get_by_username(session=db, username=username)


async def require_user_or_redirect(
    request: Request,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User | RedirectResponse:
    """Require a user or redirect to login."""
    try:
        return await get_current_user(
            request=request,
            db=db,
            user_repo=user_repo,
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=303)
        raise
