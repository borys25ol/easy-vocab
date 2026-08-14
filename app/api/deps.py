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

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    user = user_repo.get_by_username(session=db, username=payload.subject)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Logout raises the stored version, which strands every token issued
    # before it. The signature alone is not enough to trust a token.
    if user.token_version != payload.version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked",
        )
    return user


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User | None:
    """Return the authenticated user, or None when the session is unusable.

    Logout needs the user to revoke their tokens but must still clear the
    cookie for a caller whose session already expired.
    """
    try:
        return await get_current_user(request=request, db=db, user_repo=user_repo)
    except HTTPException:
        return None


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
