from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User


async def get_current_user(
    request: Request, db: Session = Depends(get_session)
) -> User:
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

    statement = select(User).where(User.username == username)
    user = db.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_optional_user(
    request: Request, db: Session = Depends(get_session)
) -> User | None:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None

    username = decode_access_token(token)
    if not username:
        return None

    statement = select(User).where(User.username == username)
    return db.exec(statement).first()


async def require_user_or_redirect(
    request: Request, db: Session = Depends(get_session)
) -> User | RedirectResponse:
    try:
        return await get_current_user(request=request, db=db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=303)
        raise
