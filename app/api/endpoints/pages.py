from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.api.deps import require_user_or_redirect
from app.models.user import User


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request, user: User | Response = Depends(require_user_or_redirect)
) -> Response:
    if isinstance(user, Response):
        return user
    return templates.TemplateResponse(request, "index.html", {"user": user})


@router.get("/quiz", response_class=HTMLResponse)
async def quiz_page(
    request: Request, user: User | Response = Depends(require_user_or_redirect)
) -> Response:
    if isinstance(user, Response):
        return user
    return templates.TemplateResponse(request, "quiz.html", {"user": user})


@router.get("/quiz_translate", response_class=HTMLResponse)
async def quiz_translate_page(
    request: Request, user: User | Response = Depends(require_user_or_redirect)
) -> Response:
    if isinstance(user, Response):
        return user
    return templates.TemplateResponse(request, "quiz_translate.html", {"user": user})


@router.get("/flashcards", response_class=HTMLResponse)
async def flashcards_page(
    request: Request, user: User | Response = Depends(require_user_or_redirect)
) -> Response:
    if isinstance(user, Response):
        return user
    return templates.TemplateResponse(request, "flashcards.html", {"user": user})


@router.get("/phrasal", response_class=HTMLResponse)
async def phrasal_page(
    request: Request, user: User | Response = Depends(require_user_or_redirect)
) -> Response:
    if isinstance(user, Response):
        return user
    return templates.TemplateResponse(request, "phrasal_verbs.html", {"user": user})


@router.get("/idioms", response_class=HTMLResponse)
async def idioms_page(
    request: Request, user: User | Response = Depends(require_user_or_redirect)
) -> Response:
    if isinstance(user, Response):
        return user
    return templates.TemplateResponse(request, "idioms.html", {"user": user})
