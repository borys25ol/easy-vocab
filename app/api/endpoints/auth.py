from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.api.deps import get_user_repository
from app.core.config import settings
from app.core.database import get_session
from app.core.security import DUMMY_PASSWORD_HASH, create_access_token, verify_password
from app.repositories.user import UserRepository


router = APIRouter()
templates_dir = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Render the login page."""
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Response:
    """Authenticate user and set session cookie."""
    user = user_repo.get_by_username(session=db, username=username)

    # Hash unconditionally. Returning early for an unknown username would
    # answer in about a millisecond instead of the ~200 ms a bcrypt round
    # takes, which tells an attacker the username exists.
    stored_hash = user.hashed_password if user else DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, stored_hash)

    if not user or not password_matches:
        if user:
            user_repo.record_failed_login(session=db, user=user)
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Invalid credentials",
            },
        )

    # The password is right, so naming the lock tells the attacker nothing
    # they could not already do. A wrong password still gets the generic
    # message above, which keeps the lock from confirming the account exists.
    if user.is_locked():
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": (
                    "Too many failed attempts. "
                    f"Try again in {settings.LOGIN_LOCKOUT_MINUTES} minutes."
                ),
            },
        )

    user_repo.clear_failed_logins(session=db, user=user)
    access_token = create_access_token(subject=user.username)
    samesite = settings.SESSION_COOKIE_SAMESITE

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
    """Clear the session cookie and redirect to the login."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    samesite = settings.SESSION_COOKIE_SAMESITE
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        samesite=samesite,
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response
