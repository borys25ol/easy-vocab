from typing import Literal, cast

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.api.deps import get_user_repository
from app.core.config import settings
from app.core.database import get_session
from app.core.security import create_access_token, verify_password
from app.repositories.user import UserRepository


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Render the login page."""
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Response:
    """Authenticate user and set session cookie."""
    user = user_repo.get_by_username(session=db, username=username)

    if not user or not verify_password(password, user.hashed_password):
        # In a real app, you'd pass an error message back to the template
        return RedirectResponse(
            url="/login?error=Invalid+credentials",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    access_token = create_access_token(subject=user.username)
    samesite = cast(
        Literal["lax", "strict", "none"] | None,
        settings.SESSION_COOKIE_SAMESITE,
    )

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=samesite,
        secure=settings.SESSION_COOKIE_SECURE,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
    )
    return response


@router.get("/logout")
async def logout() -> RedirectResponse:
    """Clear session cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    samesite = cast(
        Literal["lax", "strict", "none"] | None,
        settings.SESSION_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        samesite=samesite,
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response
